from flask import Flask, render_template, request, make_response
# import pdfkit
import pandas as pd
import os
import re
from PyPDF2 import PdfReader
import plotly.express as px
import plotly.graph_objects as go

app = Flask(__name__)

# Defining a folder to store uploaded files temporarily
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Route to render file upload form
@app.route('/')
def upload_file():
    return render_template('index.html')

# Function to extract statement period
def extract_statement_period(text):
    pattern = r'Transaction Statement for \d{10}\s+(\d{2} \w+, \d{4} - \d{2} \w+, \d{4})'
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    return "Period not found"

# Function to extract data from a single page
def extract_data_from_page(page):
    text = page.extract_text()
    pattern = r'(\w+ \d{2}, \d{4})\s+\d{2}:\d{2} [apm]{2}\s+(DEBIT|CREDIT)\s+₹([\d,.]+)\s+([^\n]+)'
    transactions = re.findall(pattern, text)
    data = []
    for transaction in transactions:
        date, trans_type, amount, details = transaction
        data.append([date, details.strip(), trans_type, amount])
    return data, text

# Route to handle file upload and process PDF
@app.route('/upload', methods=['POST'])
def upload():
    try:
        if 'file' not in request.files:
            return "No file part"

        file = request.files['file']
        if file.filename == '':
            return "No selected file"

        if file:
            # Save the uploaded file to the specified upload folder
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(pdf_path)

            # Read the PDF
            reader = PdfReader(pdf_path)

            # Extract data from all pages
            all_data = []
            full_text = ""
            for page in reader.pages:
                data, text = extract_data_from_page(page)
                all_data.extend(data)
                full_text += text

            # Extract statement period
            statement_period = extract_statement_period(full_text)

            # Create DataFrame
            columns = ['Date', 'Transaction Details', 'Type', 'Amount']
            df = pd.DataFrame(all_data, columns=columns)

            # Clean Amount column
            df['Amount'] = df['Amount'].replace('[\₹,]', '', regex=True).astype(float)

            # Categorize Transactions (Example categorization, adjust as needed)
            df['Category'] = df['Transaction Details'].apply(categorize_transaction)

            # Save to CSV
            csv_path = os.path.join(app.config['UPLOAD_FOLDER'], 'processed_data.csv')
            df.to_csv(csv_path, index=False)

            # Generate visualizations
            line_chart = create_line_chart(df)
            donut_chart = create_donut_chart(df)
            gauge_chart2 = create_gauge_chart2(df)
            gauge_chart3 = create_gauge_chart3(df)
            gauge_chart = create_gauge_chart(df)
            bar_chart = create_bar_chart(df)
            pie_chart = create_pie_chart(df)
            advanced_chart = create_advanced_chart(df)
            top_receivers_chart = create_top_receivers_chart(df)
            top_receivers_chart2= create_top_receivers_chart2(df)
            top_product=create_top_product(df)
            category_chart = create_category_chart(df)
            treemap_chart = create_treemap(df)

            
            return render_template('dashboard.html', statement_period=statement_period, line_chart=line_chart, donut_chart=donut_chart, gauge_chart2=gauge_chart2, gauge_chart3=gauge_chart3, gauge_chart=gauge_chart, bar_chart=bar_chart, pie_chart=pie_chart, advanced_chart=advanced_chart, top_receivers_chart=top_receivers_chart, top_receivers_chart2=top_receivers_chart2, top_product=top_product, category_chart=category_chart, treemap_chart=treemap_chart)

    except Exception as e:
        return f"Error processing PDF: {e}"


def categorize_transaction(details):
    categories = {
        'Food': ['restaurant', 'dining', 'cafe'],
        'Groceries': ['supermarket', 'grocery', 'mart'],
        # Add more categories as needed
    }
    for category, keywords in categories.items():
        if any(keyword.lower() in details.lower() for keyword in keywords):
            return category
    return 'Other'

# Functions for generating visualizations
def create_bar_chart(df):
    total_transactions = df.groupby('Type')['Amount'].sum().reset_index()
    fig = px.bar(total_transactions, x='Type', y='Amount', color='Type', text='Amount', title='Total Transaction Amounts by Type', labels={'Amount': 'Total Amount', 'Type': 'Transaction Type'})
    fig.update_layout(xaxis_title=None, yaxis_title='Total Amount', uniformtext_minsize=8, uniformtext_mode='hide', bargap=0.2)
    return fig.to_html(full_html=False)

def create_pie_chart(df):
    pie_data = df.groupby('Type')['Amount'].sum().reset_index()
    fig = px.pie(pie_data, values='Amount', names='Type', title='Transaction Amount by Type')
    return fig.to_html(full_html=False)

def create_advanced_chart(df):
    fig = px.sunburst(df, path=['Type', 'Transaction Details'], values='Amount', title='Transaction Details by Type')
    return fig.to_html(full_html=False)

def create_line_chart(df):
    fig = px.line(df, x='Date', y='Amount', title='Transaction Amounts Over Time')
    return fig.to_html(full_html=False)

def create_donut_chart(df):
    pie_data = df.groupby('Transaction Details')['Amount'].sum().nlargest(5).reset_index()
    fig = px.pie(pie_data, values='Amount', names='Transaction Details', title='Transaction Amount by Type', hole=0.4)
    return fig.to_html(full_html=False)

def create_gauge_chart2(df):
    total_amount = df['Amount'].sum()
    n=df['Date'].nunique()
    average=total_amount/n
    currency_symbol='₹'
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=average,
        title={'text': f"Average Trasaction per day ({currency_symbol})"},
        gauge={'axis': {'range': [None, average * 1.2]}}
    ))
    return fig.to_html(full_html=False)

def create_gauge_chart3(df):
    df_debit = df[df['Type'] == 'DEBIT']
    total_amount_debit = df_debit['Amount'].sum()
    n=df['Date'].nunique()
    average=total_amount_debit/n
    currency_symbol='₹'
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=average,
        title={'text': f"Average Debit Trasactions per day ({currency_symbol})"},
        gauge={'axis': {'range': [None, average * 1.2]}}
    ))
    return fig.to_html(full_html=False)

def create_gauge_chart(df):
    total_amount = df['Amount'].sum()
    currency_symbol = '₹' 
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=total_amount,
        title={'text': f"Total Transaction  ({currency_symbol})"},
        gauge={'axis': {'range': [None, total_amount * 1.2]}}
    ))
    return fig.to_html(full_html=False)

def create_top_receivers_chart(df):
    debit_transactions = df[df['Type'] == 'DEBIT']  # Filter to include only debit transactions
    top_receivers = debit_transactions.groupby('Transaction Details')['Amount'].sum().nlargest(5).reset_index()
    top_receivers.columns = ['Receiver', 'Total Amount']
    fig = px.bar(top_receivers, x='Receiver', y='Total Amount', title='Top 5 Receivers of Debit Transactions')
    return fig.to_html(full_html=False)

def create_top_receivers_chart2(df):
    top_receivers = df['Transaction Details'].value_counts().head(5).reset_index()
    top_receivers.columns = ['Receiver', 'Count']
    fig = px.bar(top_receivers, x='Receiver', y='Count', title='Top 5 Receivers by counts')
    return fig.to_html(full_html=False)

def create_top_product(df):
    top_products = df.groupby(['Transaction Details', 'Amount']).size().nlargest(5).reset_index(name='Count')
    top_products['Transaction Details'] = top_products['Transaction Details'] + ' - ₹' + top_products['Amount'].astype(str)
    fig = px.bar(top_products, x='Transaction Details', y='Count', title='Top 5 Products or Services by Transaction Amount')
    return fig.to_html(full_html=False)

def create_category_chart(df):
    category_data = df.groupby('Category')['Amount'].sum().reset_index()
    fig = px.bar(category_data, x='Category', y='Amount', title='Transaction Amount by Category')
    return fig.to_html(full_html=False)

def create_treemap(df):
    fig = px.treemap(df, path=['Category', 'Transaction Details'], values='Amount', title='Transaction Treemap')
    return fig.to_html(full_html=False)

if __name__ == '__main__':
    app.run(debug=True)

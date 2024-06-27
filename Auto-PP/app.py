from flask import Flask, render_template, request
import pandas as pd
import os
import re
from PyPDF2 import PdfReader
import plotly.express as px
import plotly.graph_objects as go

app = Flask(__name__)

# Define a folder to store uploaded files temporarily
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Route to render file upload form
@app.route('/')
def upload_file():
    return render_template('index.html')

# Function to extract data from a single page
def extract_data_from_page(page):
    text = page.extract_text()
    pattern = r'(\w+ \d{2}, \d{4})\s+(\d{2}:\d{2} [apm]{2})\s+(DEBIT|CREDIT)\s+₹([\d,.]+)\s+([^\n]+)'
    transactions = re.findall(pattern, text)
    data = []
    for transaction in transactions:
        date, time, trans_type, amount, details = transaction
        data.append([f"{date} {time}", details.strip(), trans_type, amount])
    return data

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
            for page in reader.pages:
                all_data.extend(extract_data_from_page(page))

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
            gauge_chart = create_gauge_chart(df)
            bar_chart = create_bar_chart(df)
            pie_chart = create_pie_chart(df)
            advanced_chart = create_advanced_chart(df)
            top_receivers_chart = create_top_receivers_chart(df)
            top_receivers_chart2= create_top_receivers_chart2(df)
            category_chart = create_category_chart(df)
            treemap_chart = create_treemap(df)

            # Render dashboard with visualizations
            return render_template('dashboard.html', line_chart=line_chart, donut_chart=donut_chart, gauge_chart=gauge_chart, bar_chart=bar_chart,
                                    pie_chart=pie_chart, advanced_chart=advanced_chart, top_receivers_chart=top_receivers_chart,
                                   top_receivers_chart2=top_receivers_chart2, category_chart=category_chart, treemap_chart= treemap_chart)

    except Exception as e:
        return f"Error processing PDF: {e}"

# Function to categorize transactions
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
    
    fig = px.bar(df, x='Type', y='Amount', title='Transaction Amounts')
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
    # pie_data = df.groupby('Type')['Amount'].sum().reset_index()
    pie_data = df.groupby('Transaction Details')['Amount'].sum().nlargest(5).reset_index()
    fig = px.pie(pie_data, values='Amount', names='Transaction Details', title='Transaction Amount by Type', hole=0.4)
    return fig.to_html(full_html=False)

def create_gauge_chart(df):
    total_amount = df['Amount'].sum()
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=total_amount,
        title={'text': "Total Transaction Amount"},
        gauge={'axis': {'range': [None, total_amount * 1.2]}}
    ))
    return fig.to_html(full_html=False)

def create_top_receivers_chart(df):
    top_receivers = df.groupby('Transaction Details')['Amount'].sum().nlargest(5).reset_index()
    top_receivers.columns = ['Receiver', 'Total Amount']
    fig = px.bar(top_receivers, x='Receiver', y='Total Amount', title='Top 5 Receivers')
    return fig.to_html(full_html=False)

def create_top_receivers_chart2(df):
    top_receivers = df['Transaction Details'].value_counts().head(5).reset_index()
    top_receivers.columns = ['Receiver', 'Count']
    fig = px.bar(top_receivers, x='Receiver', y='Count', title='Top 5 Receivers by counts')
    return fig.to_html(full_html=False)

def create_category_chart(df):
    category_data = df.groupby('Category')['Amount'].sum().reset_index()
    fig = px.pie(category_data, values='Amount', names='Category', title='Transaction Amount by Category')
    return fig.to_html(full_html=False)

def create_treemap(df):
    treemap_data = df.groupby(['Category', 'Transaction Details']).sum().reset_index()
    fig = px.treemap(treemap_data, path=['Category', 'Transaction Details'], values='Amount',
                     title='Transaction Details Treemap')
    return fig.to_html(full_html=False)

if __name__ == '__main__':
    app.run(debug=True)

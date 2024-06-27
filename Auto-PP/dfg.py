import tabula
inp=(r"uploads/PhonePe_Statement_May2024_Jun2024.pdf")
out=(r"test.csv")

df=tabula.read_pdf(input_path=inp, pages="all")
tabula.convert_into(input_path=inp,output_path=out, output_format="csv",pages="all",stream=True)

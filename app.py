import streamlit as st
from PyPDF2 import PdfReader, PdfWriter
import json
import os

st.title("PDF Form Filling")

# Option to either upload a PDF or select AR-11 form
form_option = st.radio("Choose PDF source:", ("Upload a PDF file", "Use AR-11 form"))

# If the user selects to upload a PDF file
if form_option == "Upload a PDF file":
    uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")
else:
    # Use the local AR-11 form
    ar11_form_path = "ar-11.pdf"
    if os.path.exists(ar11_form_path):
        uploaded_file = ar11_form_path
    else:
        st.error("AR-11 form not found. Please upload a PDF file instead.")
        uploaded_file = None

if uploaded_file is not None:
    # Load the PDF
    reader = PdfReader(uploaded_file) if form_option == "Upload a PDF file" else PdfReader(open(uploaded_file, "rb"))
    writer = PdfWriter()

    # Copy pages to writer
    for page in reader.pages:
        writer.add_page(page)

    # Get the form fields
    fields = reader.get_fields()

    # Create a dictionary to store text fields and their /TU values or empty string
    form_dict = {}
    for field_name, field_info in fields.items():
        if field_info.get('/FT') == '/Tx':  # '/Tx' indicates a text field
            form_dict[field_name] = field_info.get('/TU', '')

    # Initialize session state variables
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "index" not in st.session_state:
        st.session_state.index = 0
    if "form_completed" not in st.session_state:
        st.session_state.form_completed = False
    if "form_data" not in st.session_state:
        st.session_state.form_data = {}

    # Convert field names to a list for easier iteration
    form_fields = list(form_dict.keys())

    # Display previous chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Handle user input
    if st.session_state.index < len(form_fields):
        field_name = form_fields[st.session_state.index]
        field_prompt = form_dict[field_name]
        prompt = st.chat_input()
        if prompt and prompt.strip():  # Ensure the input is not empty or just whitespace
            # Display user message
            with st.chat_message("user"):
                st.markdown(f"{prompt}")
            st.session_state.messages.append({"role": "user", "content": f"{prompt}"})

            # Store the user's input in the form data
            st.session_state.form_data[field_name] = prompt

            # Increment index after user response
            st.session_state.index += 1

            # If there are more fields, prepare the next assistant message
            if st.session_state.index < len(form_fields):
                next_field_name = form_fields[st.session_state.index]
                next_field_prompt = form_dict[next_field_name]
                with st.chat_message("assistant"):
                    system_prompt = f"{next_field_prompt}"
                    st.markdown(system_prompt)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": system_prompt}
                    )
            else:
                st.session_state.form_completed = True
        else:
            st.error("Input cannot be empty. Please enter a valid response.")

    # Once all fields are completed, fill and save the PDF
    if st.session_state.form_completed:
        st.write("Form completed!")
        st.json(st.session_state.form_data)

        # Update the form fields in the PDF with the collected data
        writer.update_page_form_field_values(writer.pages[0], st.session_state.form_data)

        # Save the filled PDF
        filled_pdf_path = "filled_form.pdf"
        with open(filled_pdf_path, "wb") as output_stream:
            writer.write(output_stream)

        # Provide a download button for the filled PDF
        with open(filled_pdf_path, "rb") as file:
            st.download_button(
                label="Download filled PDF",
                data=file,
                file_name="filled_form.pdf",
                mime="application/pdf"
            )

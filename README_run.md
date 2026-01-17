# Digital Waste Analyzer — Prototype (Streamlit)

## Setup
1. Create a folder `digital-waste-analyzer`.
2. Place these files inside:
   - parser.py
   - rules.py
   - estimator.py
   - carbon.py
   - suggester.py
   - streamlit_app.py
   - requirements.txt

3. (Optional) create a virtualenv:
   python -m venv venv
   source venv/bin/activate   # linux/mac
   venv\\Scripts\\activate    # windows

4. Install requirements:
   pip install -r requirements.txt

## Run the app
streamlit run streamlit_app.py

The app will open in your browser. Upload a `.py` file or paste code and click Analyze.

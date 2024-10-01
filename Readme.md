# LawGlance: An AI Lawyer Assistant
## *Law-i with AI*

**LawGlance** is an open-source legal assistant based on **Retriever-Augmented Generation (RAG)** and Indian laws. This project aims to make legal assistance more accessible to the public by providing AI-driven legal guidance on Indian law.

This project is initiated and implemented with guidance and support from mentors at [Data Science Academy](https://datascience.one/) and professionals at [Curvelogics](https://www.curvelogics.com/).

## Laws Currently Covered

1. **The Indian Constitution**
2. **The Bharatiya Nyaya Sanhita, 2023**
3. **The Bharatiya Nagarik Suraksha Sanhita, 2023**
4. **The Bharatiya Sakshya Adhiniyam, 2023**

This project was started ad [Niyam SahaAI](https://github.com/niyam-sahaai/niyam-sahaai) and with further developments we have decided to host this as a website.

## Video Tutorial
[![Niyam SahaAI Tutorial](https://img.youtube.com/vi/sWpLEApQtvE/0.jpg)](https://www.youtube.com/watch?v=sWpLEApQtvE "Niyam SahaAI Tutorial")

## How to Use-For Developers

To get started with **LawGlance**, follow these steps:
1. Open the Command Line Interface and run the following commmand
```bash
git clone https://github.com/lawglance/lawglance.git
```
2. Change the directory to the respected folder
```bash
cd lawglance
```
3. Use the following command to install necessary packages
```bash
pip install -r requirements.txt
```
4. Open the `.env` file in normal text editing software and paste OPENAI API KEY
```bash
OPENAI API KEY = ------
``` 

5. Run the following command to use the app
```bash
python manage.py runserver
```
6. Run the following url in your browser
```bash
 http://127.0.0.1:8000/
```
## Tools & Technologies Used

- **LangChain**
- **ChromaDB**
- **Streamlit**
- **OpenAI API**

## Planned Future Developments

1. **Develop LawGlance into a fully functional service with a user-friendly frontend**
2. **Expand LawGlance to support legal systems in more countries like Canada**
3. **Broader Data Sources**  
   - Supreme Court Judgments  
   - Women-Centric Laws  
   - Consumer Protection Laws  
   - Pollution Laws  

4. **Voice Integration**  
5. **Multi-Lingual Support**




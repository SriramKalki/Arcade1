import os
import sqlite3
from dotenv import load_dotenv
import openai
from langchain.chains import create_sql_query_chain
from langchain_openai import ChatOpenAI
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from operator import itemgetter
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough

load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')
openai.api_key = openai_api_key
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
db = SQLDatabase.from_uri('sqlite:///weather.db')
generate_query = create_sql_query_chain(llm, db)
execute_query = QuerySQLDataBaseTool(db=db)

answer_prompt = PromptTemplate.from_template(
    """Given the following user question, corresponding SQL query, and SQL result, answer the user question.

Question: {question}
SQL Query: {query}
SQL Result: {result}
Answer: """
)
 
def process_query(query):
    rephrase_answer = answer_prompt | llm | StrOutputParser()

    chain = (
        RunnablePassthrough.assign(query=generate_query).assign(
            result=itemgetter("query") | execute_query
        )
        | rephrase_answer
    )

    return chain.invoke({"question": query })    

def process_file(file_path):
    conn = sqlite3.connect('weather.db')
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS weather (
            date TEXT,
            weather_code REAL,
            temperature_max REAL,
            temperature_min REAL,
            precipitation_sum REAL,
            wind_speed_max REAL,
            precipitation_probability_max REAL
        )
    ''')

    c.execute('DELETE FROM weather')

    with open(file_path,'r') as f:
        lines = f.readlines()
        data = {}
        for line in lines:
            key, values = line.split(':')
            values = values.strip().split()
            if key == 'date':
                data['date'] = values
            else:
                if key not in data:
                    data[key] = values
                else:
                    data[key].extend(values)        
        
        for i in range(len(data['date'])):
            c.execute('''
            INSERT INTO weather (date, weather_code, temperature_max, temperature_min, precipitation_sum, wind_speed_max, precipitation_probability_max)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
            data['date'][i],
            data['weather_code'][i] if 'weather_code' in data else None,
            data['temperature_max'][i] if 'temperature_max' in data else None,
            data['temperature_min'][i] if 'temperature_min' in data else None,
            data['precipitation_sum'][i] if 'precipitation_sum' in data else None,
            data['wind_speed_max'][i] if 'wind_speed_max' in data else None,
            data['precipitation_probability_max'][i] if 'precipitation_probability_max' in data else None
            ))
        
        conn.commit()
        conn.close()
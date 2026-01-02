import streamlit as st
import psycopg2
import os
from dotenv import load_dotenv
from google import genai
import pandas as pd

# Load environment variables
load_dotenv()

# Configure Gemini
api_key = os.getenv("GOOGLE_API_KEY")
print("api_key:", api_key)  # Debugging line to check if the API key is loaded
if not api_key:
    st.error("GOOGLE_API_KEY not found in .env file. Please set it.")
    st.stop()

try:
    # Newer versions of the Google GenAI SDK use a Client object instead of a global configure function.
    # Create a client and store the default model id.
    client = genai.Client(api_key=api_key)
    model_id = os.getenv("MODEL_ID", "gemini-1.5-flash")
except Exception as e:
    st.error(f"Failed to initialize Gemini client: {e}")
    st.info("Please ensure you have the 'google-genai' package installed and your API key is correct.")
    st.stop()


def get_db_schema():
    """Connects to the database and retrieves the schema of the tables."""
    schema_info = ""
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="postgres",
            host=os.getenv("DB_HOST", "localhost"),
            port="5432"
        )
        cur = conn.cursor()

        # Get all tables
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
        tables = cur.fetchall()

        for table in tables:
            table_name = table[0]
            schema_info += f"Table '{table_name}':\n"
            cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}';")
            columns = cur.fetchall()
            for column in columns:
                schema_info += f"  - {column[0]} ({column[1]})\n"
            schema_info += "\n"

        cur.close()
        conn.close()
        return schema_info
    except psycopg2.OperationalError as e:
        st.error(f"Could not connect to the database: {e}")
        st.error("Please ensure the PostgreSQL container is running.")
        return None
    except Exception as e:
        st.error(f"An error occurred while fetching the schema: {e}")
        return None

def main():
    """Main function for the Streamlit chatbot application."""
    st.set_page_config(page_title="NL-to-SQL Chatbot", page_icon=":robot_face:")
    st.title("Natural Language to SQL Chatbot")
    st.write("Ask questions about your database in plain English!")

    # Get database schema
    schema = get_db_schema()
    if not schema:
        st.stop()

    # User input
    user_question = st.text_area("Your question:")

    if st.button("Generate SQL and Run"):
        if not user_question:
            st.warning("Please enter a question.")
            st.stop()

        with st.spinner("Generating SQL query..."):
            # Construct the prompt
            prompt = f"""
            You are a PostgreSQL expert. Given the following database schema, please generate a SQL query to answer the user's question.

            **Schema:**
            {schema}

            **Question:**
            {user_question}

            **SQL Query (PostgreSQL):**
            """

            try:
                # Generate SQL query via the Client API
                response = client.models.generate_content(model=model_id, contents=prompt)

                # Extract text from response (robust to different response shapes)
                sql_parts = []
                if getattr(response, 'candidates', None):
                    candidate = response.candidates[0]
                    if getattr(candidate, 'content', None) and getattr(candidate.content, 'parts', None):
                        for part in candidate.content.parts:
                            if getattr(part, 'text', None):
                                sql_parts.append(part.text)
                sql_query = "".join(sql_parts).strip().replace("```sql", "").replace("```", "").strip()

                st.subheader("Generated SQL Query:")
                st.code(sql_query, language="sql")

                # Execute the query
                with st.spinner("Executing query..."):
                    conn = psycopg2.connect(
                        dbname="postgres",
                        user="postgres",
                        password="postgres",
                        host="localhost",
                        port="5432"
                    )
                    cur = conn.cursor()
                    cur.execute(sql_query)
                    
                    results = cur.fetchall()
                    column_names = [desc[0] for desc in cur.description]

                    cur.close()
                    conn.close()

                st.subheader("Query Results:")
                if results:
                    try:
                        df = pd.DataFrame(results, columns=column_names)
                        st.dataframe(df)
                    except Exception as e:
                        st.error(f"Could not render results as a table: {e}")
                        st.write(results)
                else:
                    st.success("Query executed successfully, but returned no results.")

            except Exception as e:
                st.error(f"An error occurred: {e}")


if __name__ == "__main__":
    main()

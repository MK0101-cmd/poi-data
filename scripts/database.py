import psycopg2
from psycopg2.extras import execute_values, RealDictCursor
from pgvector.psycopg2 import register_vector
from contextlib import contextmanager
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.conn_params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'poi_rag'),
            'user': os.getenv('DB_USER', 'poi_user'),
            'password': os.getenv('DB_PASSWORD'),
        }
    
    @contextmanager
    def get_connection(self):
        conn = psycopg2.connect(**self.conn_params)
        register_vector(conn)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @contextmanager
    def get_cursor(self, dict_cursor=True):
        with self.get_connection() as conn:
            cursor_factory = RealDictCursor if dict_cursor else None
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
            finally:
                cursor.close()
    
    def insert_document(self, doc_data):
        with self.get_cursor() as cur:
            cur.execute("""
                INSERT INTO documents 
                (file_path, file_name, content, content_type, category, subcategory, 
                 content_subtype, hierarchy_path, depth)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                doc_data['file_path'],
                doc_data['file_name'],
                doc_data['content'],
                doc_data['content_type'],
                doc_data['category'],
                doc_data['subcategory'],
                doc_data.get('content_subtype'),
                doc_data['hierarchy_path'],
                doc_data['depth']
            ))
            return cur.fetchone()['id']
    
    def insert_chunks_batch(self, chunks):
        with self.get_cursor() as cur:
            execute_values(cur, """
                INSERT INTO document_chunks 
                (document_id, chunk_text, chunk_index, chunk_tokens, 
                 section_title, section_type, embedding)
                VALUES %s
            """, [
                (
                    chunk['document_id'],
                    chunk['chunk_text'],
                    chunk['chunk_index'],
                    chunk.get('chunk_tokens'),
                    chunk.get('section_title'),
                    chunk.get('section_type'),
                    chunk['embedding']
                )
                for chunk in chunks
            ])
    
    def search_vector(self, query_embedding, limit=10, threshold=0.7):
        with self.get_cursor() as cur:
            cur.execute("""
                SELECT 
                    dc.id as chunk_id,
                    dc.document_id,
                    dc.chunk_text,
                    dc.section_title,
                    d.category,
                    d.subcategory,
                    1 - (dc.embedding <=> %s) as similarity_score
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                WHERE 1 - (dc.embedding <=> %s) > %s
                ORDER BY dc.embedding <=> %s
                LIMIT %s
            """, (query_embedding, query_embedding, threshold, query_embedding, limit))
            return cur.fetchall()

# Test connection
if __name__ == "__main__":
    db = Database()
    with db.get_cursor() as cur:
        cur.execute("SELECT version()")
        print(f"✓ Connected to PostgreSQL: {cur.fetchone()['version']}")


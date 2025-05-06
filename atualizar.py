# Para atualizações futuras do banco de dados

import sqlite3

# Conectar ao banco de dados
conn = sqlite3.connect('instance/banco.db')
cursor = conn.cursor()

# Adicionar a coluna 'tipo_usuario' à tabela 'usuarios'
cursor.execute('ALTER TABLE usuarios ADD COLUMN tipo_usuario TEXT')

conn.commit()
conn.close()

print("Coluna 'tipo_usuario' adicionada com sucesso!")

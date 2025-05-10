import sqlite3

# Conectar ao banco de dados
conn = sqlite3.connect('instance/banco.db')
cursor = conn.cursor()

# Adicionar a coluna 'usuario_id' à tabela 'imoveis'
cursor.execute('ALTER TABLE imoveis ADD COLUMN usuario_id INTEGER')

conn.commit()
conn.close()

print("Coluna 'usuario_id' adicionada com sucesso!")

# Verificar se a tabela imoveis existe
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='imoveis'")
table_exists = cursor.fetchone()

if not table_exists:
    # Criar a tabela imoveis com id como chave primária
    cursor.execute('''
    CREATE TABLE imoveis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT,
        endereco TEXT,
        bairro TEXT,
        numero TEXT,
        cep TEXT,
        complemento TEXT,
        valor TEXT,
        quartos INTEGER,
        banheiros INTEGER,
        inclusos TEXT,
        outros TEXT,
        descricao TEXT,
        usuario_id INTEGER,
        fotos TEXT
    )
    ''')
    print("Tabela 'imoveis' criada com sucesso!")
else:
    # Verificar se a coluna id já existe
    cursor.execute("PRAGMA table_info(imoveis)")
    columns = cursor.fetchall()
    id_exists = any(column[1] == 'id' for column in columns)
    
    if not id_exists:
        # Criar uma tabela temporária com a estrutura desejada
        cursor.execute('''
        CREATE TABLE imoveis_temp (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT,
            endereco TEXT,
            bairro TEXT,
            numero TEXT,
            cep TEXT,
            complemento TEXT,
            valor TEXT,
            quartos INTEGER,
            banheiros INTEGER,
            inclusos TEXT,
            outros TEXT,
            descricao TEXT,
            usuario_id INTEGER,
            fotos TEXT
        )
        ''')
        
        # Copiar dados da tabela antiga para a nova
        cursor.execute("INSERT INTO imoveis_temp (tipo, endereco, bairro, numero, cep, complemento, valor, quartos, banheiros, inclusos, outros, descricao, usuario_id, fotos) SELECT tipo, endereco, bairro, numero, cep, complemento, valor, quartos, banheiros, inclusos, outros, descricao, usuario_id, fotos FROM imoveis")
        
        # Remover tabela antiga
        cursor.execute("DROP TABLE imoveis")
        
        # Renomear a tabela temporária
        cursor.execute("ALTER TABLE imoveis_temp RENAME TO imoveis")
        
        print("Coluna 'id' adicionada à tabela 'imoveis' com sucesso!")
    else:
        print("A coluna 'id' já existe na tabela 'imoveis'.")

conn.commit()
conn.close()

print("Operação concluída com sucesso!")


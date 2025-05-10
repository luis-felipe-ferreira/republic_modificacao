from flask import Flask, render_template, request, redirect, url_for, session, g, jsonify
import sqlite3
import os
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'
DATABASE = 'instance/banco.db'

# ----- UTILITÁRIOS DE BANCO DE DADOS -----


def get_db():
    if 'db' not in g:
        os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# ----- CONTEXTO GLOBAL -----


@app.context_processor
def inject_usuario():
    usuario_nome = tipo_usuario = None
    user_id = session.get('usuario_id')
    if user_id:
        db = get_db()
        cur = db.execute(
            'SELECT nome, tipo_usuario FROM usuarios WHERE id = ?', (user_id,)
        )
        row = cur.fetchone()
        if row:
            usuario_nome = row['nome']
            tipo_usuario = row['tipo_usuario']
    return dict(usuario_nome=usuario_nome, tipo_usuario=tipo_usuario)

# ----- DECORATOR LOGIN -----


def login_required(f):
    from functools import wraps

    @wraps(f)
    def wrapped(*args, **kwargs):
        if 'usuario_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapped

# ----- ROTAS -----


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/sobre')
def sobre():
    return render_template('sobre.html')


@app.route('/termos')
def termos():
    return render_template('termos.html')


@app.route('/pesquisa')
def pesquisa():
    db = get_db()
    rows = db.execute(
        """
        SELECT id, tipo, quartos, valor, endereco, inclusos, imagem
        FROM imoveis
        WHERE ativo = 1
        """
    ).fetchall()
    imoveis = []
    for r in rows:
        imoveis.append({
            'id': r['id'],
            'tipo': r['tipo'],
            'quartos': r['quartos'],
            'valor': r['valor'],
            'endereco': r['endereco'],
            'inclusos': r['inclusos'].split(',') if r['inclusos'] else [],
            'imagens': r['imagem'].split(',') if r['imagem'] else ['default.jpg'],
        })
    return render_template('pesquisa.html', imoveis=imoveis)


@app.route('/detalhes_imovel/<int:id>')
def detalhes_imovel(id):
    db = get_db()
    r = db.execute(
        """
        SELECT *, (SELECT nome FROM usuarios WHERE id = imoveis.usuario_id) AS dono
        FROM imoveis WHERE id = ?
        """, (id,)
    ).fetchone()
    if not r:
        return "Imóvel não encontrado", 404
    apt = dict(r)
    apt['inclusos'] = apt['inclusos'].split(',') if apt['inclusos'] else []
    apt['imagens'] = apt['imagem'].split(
        ',') if apt['imagem'] else ['default.jpg']
    return render_template('apt.html', apartamento=apt, dono_nome=apt['dono'], usuario_logado=session.get('usuario_id'))


@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    mensagem_cadastro = mensagem_login = None
    if request.method == 'POST' and 'nome' in request.form:
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        celular = request.form['celular']
        tipo_usuario = request.form['tipo_usuario']
        db = get_db()
        try:
            db.execute(
                'INSERT INTO usuarios (nome, email, senha, celular, tipo_usuario) VALUES (?, ?, ?, ?, ?)',
                (nome, email, senha, celular, tipo_usuario)
            )
            db.commit()
            mensagem_cadastro = 'Cadastro realizado com sucesso!'
        except sqlite3.IntegrityError:
            mensagem_cadastro = 'Email já cadastrado.'
    return render_template('cadastro.html', mensagem_cadastro=mensagem_cadastro, mensagem_login=mensagem_login)


@app.route('/login', methods=['GET', 'POST'])
def login():
    mensagem_login = mensagem_cadastro = None
    if request.method == 'POST' and 'email' in request.form:
        email = request.form['email']
        senha = request.form['senha']
        db = get_db()
        user = db.execute(
            'SELECT id FROM usuarios WHERE email = ? AND senha = ?', (
                email, senha)
        ).fetchone()
        if user:
            session['usuario_id'] = user['id']
            return redirect(url_for('index'))
        mensagem_login = 'Email ou senha inválidos!'
    return render_template('cadastro.html', mensagem_login=mensagem_login, mensagem_cadastro=mensagem_cadastro)


@app.route('/logout')
def logout():
    session.pop('usuario_id', None)
    return redirect(url_for('cadastro'))


@app.route('/cadastro_imovel', methods=['GET', 'POST'])
@login_required
def cadastro_imovel():
    db = get_db()
    tipo = db.execute('SELECT tipo_usuario FROM usuarios WHERE id = ?',
                      (session['usuario_id'],)).fetchone()[0]
    if tipo != 'anunciante':
        return "Apenas anunciantes podem acessar esta página.", 403
    if request.method == 'POST':
        data = request.form.to_dict()
        inclusos = request.form.getlist('inclusos')
        files = request.files.getlist('fotos')
        nomes = []
        for f in files:
            if f.filename:
                fn = secure_filename(f.filename)
                path = os.path.join('static/img/imoveis', fn)
                f.save(path)
                nomes.append(fn)
        if not nomes:
            nomes = ['default.jpg']
        db.execute(
            '''INSERT INTO imoveis (endereco, bairro, numero, cep, complemento,
                                   valor, quartos, banheiros, inclusos,
                                   outros, descricao, imagem, tipo, usuario_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (*[data.get(k) for k in ['endereco', 'bairro', 'numero', 'cep', 'complemento']],
             float(data['valor'].replace(',', '.')),
             int(data['quartos']), int(data['banheiros']),
             ','.join(inclusos), data.get(
                 'outros', ''), data.get('descricao', ''),
             ','.join(nomes), data['tipo'], session['usuario_id'])
        )
        db.commit()
        return redirect(url_for('pesquisa'))
    return render_template('cadastro_imovel.html')


@app.route('/meus_imoveis')
@login_required
def meus_imoveis():
    rows = get_db().execute(
        'SELECT id, endereco, bairro, valor, tipo, imagem, ativo FROM imoveis WHERE usuario_id = ?',
        (session['usuario_id'],)
    ).fetchall()
    return render_template('meus_imoveis.html', imoveis=rows)

# --- ROTAS EDITAR IMOVEIS --- #

@app.route('/editar_imovel/<int:id>', methods=['GET'])
@login_required
def pagina_edicao(id):
    db = get_db()
    apt = db.execute(
        'SELECT valor, descricao FROM imoveis WHERE id = ? AND usuario_id = ?',
        (id, session['usuario_id'])
    ).fetchone()

    if not apt:
        return "Imóvel não encontrado ou não autorizado", 404

    return render_template('editar_imovel.html', id=id)

@app.route('/api/imovel/<int:id>')
@login_required
def obter_imovel(id):
    db = get_db()
    imovel = db.execute(
        'SELECT * FROM imoveis WHERE id = ? AND usuario_id = ?',
        (id, session['usuario_id'])
    ).fetchone()

    if not imovel:
        return jsonify({'erro': 'Imóvel não encontrado'}), 404

    fotos = []  # Aqui coloque a lógica para retornar URLs das fotos, se tiver

    return jsonify({
        'id': imovel['id'],
        'tipo': imovel['tipo'],
        'endereco': imovel['endereco'],
        'bairro': imovel['bairro'],
        'numero': imovel['numero'],
        'cep': imovel['cep'],
        'complemento': imovel['complemento'],
        'valor': imovel['valor'],
        'quartos': imovel['quartos'],
        'banheiros': imovel['banheiros'],
        'inclusos': imovel['inclusos'].split(',') if imovel['inclusos'] else [],
        'outros': imovel['outros'],
        'descricao': imovel['descricao'],
        'fotos': fotos
    })

@app.route('/api/imoveis/<int:id>', methods=['PUT'])
@login_required
def atualizar_imovel(id):
    db = get_db()
    dados_json = request.form.get('dados')
    if not dados_json:
        return 'Dados inválidos', 400

    try:
        dados = json.loads(dados_json)
    except:
        return 'Erro ao decodificar JSON', 400

    db.execute('''
        UPDATE imoveis
        SET tipo = ?, endereco = ?, bairro = ?, numero = ?, cep = ?, complemento = ?, valor = ?, 
            quartos = ?, banheiros = ?, inclusos = ?, outros = ?, descricao = ?
        WHERE id = ? AND usuario_id = ?
    ''', (
        dados.get('tipo'),
        dados.get('endereco'),
        dados.get('bairro'),
        dados.get('numero'),
        dados.get('cep'),
        dados.get('complemento'),
        dados.get('valor'),
        dados.get('quartos'),
        dados.get('banheiros'),
        ','.join(dados.get('inclusos', [])),
        dados.get('outros'),
        dados.get('descricao'),
        id,
        session['usuario_id']
    ))
    db.commit()

    # Aqui você pode salvar novas fotos: request.files.getlist('novas_fotos')
    return '', 204


@app.route('/excluir_imovel/<int:id>', methods=['POST'])
@login_required
def excluir_imovel(id):
    db = get_db()
    db.execute('DELETE FROM imoveis WHERE id = ? AND usuario_id = ?',
               (id, session['usuario_id']))
    db.commit()
    return redirect(url_for('meus_imoveis'))


@app.route('/parar_anuncio/<int:id>', methods=['POST'])
@login_required
def parar_anuncio(id):
    db = get_db()
    db.execute('UPDATE imoveis SET ativo = 0 WHERE id = ? AND usuario_id = ?',
               (id, session['usuario_id']))
    db.commit()
    return redirect(url_for('meus_imoveis'))


@app.route('/ativar_anuncio/<int:id>', methods=['POST'])
@login_required
def ativar_anuncio(id):
    db = get_db()
    db.execute('UPDATE imoveis SET ativo = 1 WHERE id = ? AND usuario_id = ?',
               (id, session['usuario_id']))
    db.commit()
    return redirect(url_for('meus_imoveis'))

# ----- INICIALIZAÇÃO DO BANCO -----


def inicializar_banco():
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    db = sqlite3.connect(DATABASE)
    cur = db.cursor()
    # Usuários
    cur.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL,
            celular TEXT,
            tipo_usuario TEXT
        )
    ''')
    # Imóveis
    cur.execute('''
        CREATE TABLE IF NOT EXISTS imoveis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            endereco TEXT, bairro TEXT, numero TEXT, cep TEXT,
            complemento TEXT, valor REAL, quartos INTEGER,
            banheiros INTEGER, inclusos TEXT, outros TEXT,
            descricao TEXT, imagem TEXT, tipo TEXT,
            usuario_id INTEGER, ativo INTEGER DEFAULT 1,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')
    db.commit()
    db.close()


# Inicializa banco e executa a aplicação
inicializar_banco()


@app.route('/api/imovel/<int:id>')
@login_required
def api_get_imovel(id):
    db = get_db()
    imovel = db.execute(
        'SELECT * FROM imoveis WHERE id = ? AND usuario_id = ?',
        (id, session['usuario_id'])
    ).fetchone()

    if not imovel:
        return {"erro": "Imóvel não encontrado"}, 404

    return {
        "id": imovel["id"],
        "tipo": imovel["tipo"],
        "endereco": imovel["endereco"],
        "bairro": imovel["bairro"],
        "numero": imovel["numero"],
        "cep": imovel["cep"],
        "complemento": imovel["complemento"],
        "valor": imovel["valor"],
        "quartos": imovel["quartos"],
        "banheiros": imovel["banheiros"],
        "inclusos": imovel["inclusos"].split(',') if imovel["inclusos"] else [],
        "outros": imovel["outros"],
        "descricao": imovel["descricao"],
        "fotos": imovel["imagem"].split(',') if imovel["imagem"] else []
    }


if __name__ == '__main__':
    app.run(debug=True)

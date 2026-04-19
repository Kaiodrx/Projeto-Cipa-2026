import os
import uuid
import base64
from flask import current_app
from ..constants import ALLOWED_EXTENSIONS


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def salvar_foto(file):
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    return f"/static/uploads/{filename}"


def deletar_foto(url):
    if not (url and url.startswith('/static/uploads/')):
        return
    filename = url[len('/static/uploads/'):]
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if os.path.isfile(filepath):
        os.remove(filepath)


def migrar_base64(candidato):
    if not (candidato.foto and candidato.foto.startswith('data:')):
        return False
    try:
        header, data = candidato.foto.split(',', 1)
        ext = 'png' if 'png' in header else 'gif' if 'gif' in header else 'jpg'
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        with open(filepath, 'wb') as f:
            f.write(base64.b64decode(data))
        candidato.foto = f"/static/uploads/{filename}"
        return True
    except Exception:
        return False

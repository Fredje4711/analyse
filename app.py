import os
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename

# Importeren van onze parseerlogica uit lees_pdf_4.py
# Zorg ervoor dat lees_pdf_4.py in dezelfde map staat als app.py
import lees_pdf_4 as pdf_parser # We geven het een kortere naam 'pdf_parser'

# --- Flask App Configuratie ---
app = Flask(__name__)

# Configuratie voor bestandsuploads
UPLOAD_FOLDER = 'uploads' # Een map om tijdelijk PDF's op te slaan
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16MB max bestandsgrootte

# Zorg ervoor dat de upload map bestaat
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- API Endpoint voor PDF Analyse ---
@app.route('/analyze', methods=['POST'])
def analyze_pdf_endpoint():
    if 'pdfFile' not in request.files:
        return jsonify({"error": "Geen PDF-bestand deel van het request"}), 400
    
    file = request.files['pdfFile']
    
    if file.filename == '':
        return jsonify({"error": "Geen PDF-bestand geselecteerd"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename) # Veilige bestandsnaam
        # Sla het bestand tijdelijk op (optioneel, kan ook in-memory verwerkt worden)
        pdf_pad = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(pdf_pad)

        try:
            # Gebruik de functies uit onze geïmporteerde module
            geextraheerde_tekst = pdf_parser.extraheer_tekst_van_pdf(pdf_pad)
            
            if geextraheerde_tekst:
                # Geef de MARKER_KENNISBANK mee aan de parseerfunctie
                # De debug pdf naam is hier minder relevant, maar kan nog steeds meegegeven worden
                resultaten = pdf_parser.parseer_bloedwaarden(geextraheerde_tekst, pdf_parser.MARKER_KENNISBANK, huidige_pdf_naam_voor_debug=filename)
                
                # Verwijder het tijdelijke bestand na verwerking
                # os.remove(pdf_pad) # Goede praktijk, maar wacht hiermee voor debuggen
                
                return jsonify(resultaten) # Stuur de resultaten als JSON terug
            else:
                # os.remove(pdf_pad) # Ook hier
                return jsonify({"error": "Kon geen tekst extraheren uit de PDF"}), 500
        except Exception as e:
            # os.remove(pdf_pad) # Ook hier
            print(f"Fout tijdens verwerking PDF: {e}") # Log de fout op de server
            return jsonify({"error": f"Interne serverfout tijdens verwerking: {str(e)}"}), 500
        finally:
            # Zorg ervoor dat het tijdelijke bestand altijd wordt verwijderd, zelfs na een fout
            # (behalve als je het wilt bewaren voor debuggen)
            if os.path.exists(pdf_pad):
                 os.remove(pdf_pad)


    return jsonify({"error": "Ongeldig bestandstype"}), 400

# --- Route voor de Hoofdpagina (HTML) ---
@app.route('/')
def index():
    return render_template('index.html') # NU SERVEREN WE DE HTML
# --- Start de Flask Ontwikkelingsserver ---
if __name__ == '__main__':
    app.run(debug=True) # debug=True is handig tijdens ontwikkelen
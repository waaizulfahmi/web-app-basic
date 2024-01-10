from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from werkzeug.security import check_password_hash, generate_password_hash
import numpy as np
import pandas as pd
import pickle
import joblib
import math

app = Flask(__name__)

# database
app.secret_key = 'kuncisecret'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'db_prediction'
mysql = MySQL(app)

@app.route('/')
def index():
    if 'loggedin' in session:
        return render_template('index.html')
    flash('Harap Login Terlebih dahulu', 'danger')
    return redirect(url_for('login'))

@app.route('/registrasi', methods=('GET', 'POST'))
def registrasi():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        level = request.form['level']

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM tb_login WHERE username=%s OR email=%s', (username, email, ))
        akun = cursor.fetchone()
        if akun is None:
            cursor.execute('INSERT INTO tb_login (username, email, password, level) VALUES (%s, %s, %s, %s)', (username, email, generate_password_hash(password), level))
            mysql.connection.commit()
            flash('Registration Successful... Please Click Login', 'success')
        else :
            flash('Username or Email already exists.. Please Try Again', 'danger')
    return render_template('registrasi.html')

@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM tb_login WHERE email=%s', (email, ))
        akun = cursor.fetchone()
        if akun is None:
            flash('Login Failed!!! Check Your Username', 'danger')
        elif not check_password_hash(akun[3], password):
            flash('Login Failed!!! Check Your Password', 'danger')
        else:
            session['loggedin'] =  True
            session['username'] = akun[1]
            session['level'] = akun[4]
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/stroke_calc')
def stroke_calc():
    return render_template('stroke_calc.html')

@app.route('/stroke_diagnose')
def stroke_diagnose():
    return render_template('stroke_diagnosis.html')

#

@app.route('/prediksi_lama_rawat_inap')
def prediksi_lama_rawat_inap():
    return render_template('prediksi_lama_rawat_inap.html')

@app.route('/result_stroke_calc', methods = ['POST'])
def result_stroke_calc():
    if request.method == 'POST':
        usia = int(request.form['usia'])
        if int(usia) <= 20:
            umur = 0
        else:
            umur = usia -20
        jenis_kelamin = int(request.form['jenis_kelamin'])
        jenjang_pendidikan = int(request.form['jenjang_pendidikan'])
        ginjal = int(request.form['ginjal'])
        diabetes = int(request.form['diabetes'])
        jantung = int(request.form['jantung'])
        arteri_perifer = int(request.form['arteri_perifer'])
        darah_tinggi = int(request.form['darah_tinggi'])
        penyakit_jantung = int(request.form['penyakit_jantung'])
        status_merokok = int(request.form['status_merokok'])
        aktivitas_fisik = int(request.form['aktivitas_fisik'])

        total = umur + jenis_kelamin + jenjang_pendidikan + ginjal + diabetes + jantung + arteri_perifer + darah_tinggi + penyakit_jantung + status_merokok + aktivitas_fisik
        total_skor = total / 10 
        nilai_e = math.exp(total_skor)
        hitung_resiko = (1-0.99982)*nilai_e
        persentase_resiko = hitung_resiko * 100
        persen_resiko = f"{persentase_resiko:.2f}"
        return render_template('result_calc.html', persen_resiko=persen_resiko)


symptom_map = {
    'G001': 'Hemiparese Sinistra (Kelemahan anggota gerak kiri)',
    'G002': 'Penurunan kesadaran',
    'G003': 'Nyeri kepala',
    'G004': 'Hemiparese Dextra (Kelemahan anggota gerak kanan)',
    'G005': 'Afasia motorik (Bicara pelo)',
    'G006': 'Badan lemas',
    'G007': 'Gaduh gelisah',
    'G008': 'Merokok',
    'G009': 'Memiliki riwayat penyakit ginjal',
    'G010': 'Memiliki riwayat penyakit Diabetes Melitus',
}

penyakit_map = {
    'S1': {
        'name': 'Intra Cerebral Hemoragi',
        'definition': 'Intra Cerebral Hemoragi adalah pendarahan kedalam substansi otak.',
        'symptoms': ['G001', 'G002', 'G008'],
        'teraphy' : '''Terapi atau pengobatan yang dapat dilakukan adalah sebagai berikut:
                        1.	Dapat mengkonsumsi Obat Manitol untuk membantu mengurangi penumpukan cairan ditubuh dan menurunkan tekanan darah tinggi.
                        2.	Dapat mengkonsumsi Obat Citicholin untuk mengatasi gangguan ingatan.'''
    },
    'S2': {
        'name': 'Sub Arachnoid Hemoragi',
        'definition': 'Sub Arachnoid Hemoragi adalah pendarahan di dalam ruang subarachnoid yang merupakan area antara otak dan jaringan yang menutupi otak.',
        'symptoms': ['G002'],
        'teraphy' : ''' Terapi atau pengobatan yang dapat dilakukan adalah sebagai berikut: 
                        1.	Dapat mengkonsumsi obat Nicardipin untuk menurunkan tekanan darah pada hipertensi.
                        2.	Dapat mengkonsumsi obat Ceftriaxon atau antibiotik golongan sefalosporin.
                        3.	Dapat mengkonsumsi obat Manitol untuk membantu mengurangi penumpukan cairan ditubuh dan menurunkan tekanan darah tinggi. 
                        4.	Dapat mengkonsumsi obat Citicholin untuk mengatasi gangguan memori dan perilaku'''
    },
    'S3': {
        'name': 'Lacunar Infark',
        'definition': 'Lacunar Infark adalah stroke yang menyerang pembuluh darah di otak sehingga suplai aliran darah di otak menjadi terhambat.',
        'symptoms': ['G001', 'G002', 'G003', 'G004', 'G005', 'G006'],
        'teraphy' : '''Terapi atau pengobatan yang dapat dilakukan adalah sebagai berikut:
                        1.	Dapat mengkonsumsi obat Citicholin untuk mengatasi gangguan ingatan.
                        2.	Dapat mengkonsumsi obat Furosemid untuk mengurangi cairan berlebihan dalam tubuh. 
                        3.	Dapat mengkonsumsi obat Mecobalami atau Vitamin B12. 
                        4.	Dapat mengkonsumsi obat Manitol untuk membantu mengurangi penumpukan cairan ditubuh dan menurunkan tekanan darah tinggi. 
                        5.	Dapat mengkonsumsi obat Clopidogrel untuk membantu agar sel darah terutama trombosit tidak menyatu atau menggumpal. 
                        6.	Dapat mengkonsumsi obat Ceftriaxon atau antibiotik golongan sefalosporin.'''
    },
    'S4': {
        'name': 'Infark Cerebri',
        'definition': 'Infark Cerebri adalah kematian sel-sel otak yang disebabkan kekurangan oksigen. Keadaan ini sering disebut dengan stroke.',
        'symptoms': ['G001', 'G002', 'G004', 'G005'],
        'teraphy' : '''Terapi atau pengobatan yang dapat dilakukan adalah sebagai berikut:
                        1.	Dapat mengkonsumsi obat Ceftazidim (obat antibiotik) untuk mengobati infeksi bakteri.
                        2.	Dapat mengkonsumsi obat Valsartan untuk mengatasi hipertensi dan gagal jantung. 
                        3.	Dapat mengkonsumsi obat Citicholin untuk mengatasi gangguan ingatan. 
                        4.	Dapat mengkonsumsi obat Furosemid untuk mengurangi cairan berlebihan dalam tubuh. 
                        5.	Dapat mengkonsumsi obat Mecobalami atau Vitamin B12.
                        6.	Dapat mengkonsumsi obat Manitol untuk membantu mengurangi penumpukan cairan ditubuh dan menurunkan tekanan darah tinggi. 
                        7.	Dapat mengkonsumsi obat Clopidogrel untuk membantu agar sel darah terutama trombosit tidak menyatu atau menggumpal. 
                        8.	Dapat mengkonsumsi obat Ceftriaxon atau antibiotik golongan sefalosporin. 
                        9.	Dapat mengkonsumsi obat Haloperidol untuk mengembalikan keseimbangan zat kimia alami didalam otak. 
                        10.	Dapat mengkonsumsi obat Phenitoin untuk mengendalikan kejang. 
                        11.	Dapat mengkonsumsi obat Meropenem atau obat antibiotik untuk menghentikan pertumbuhan dan perkembangan bakteri.'''
    },
    'S5': {
        'name': 'Stroke Unspecified',
        'definition': 'Stroke yang tanpa spesifikasi.',
        'symptoms': ['G001', 'G004'],
        'teraphy' : '''Terapi atau pengobatan yang dapat dilakukan adalah sebagai berikut: 
                        1.	Dapat mengkonsumsi obat Citicholin untuk mengatasi ganguan memori atau perilaku.
                        2.	Dapat mengkonsumsi obat Mecobalami (Vitamin B12).'''
    },
}

@app.route('/result_stroke_diagnosis', methods=['POST'])
def result_stroke_diagnosis():
    if request.method == 'POST':
        selected_symptoms = request.form.getlist('symptom')


        matched_diseases = []
        for disease_code, disease_info in penyakit_map.items():
            if selected_symptoms == disease_info['symptoms'] :
                matched_diseases.append(disease_code)

        if matched_diseases:
            match_disease = [f"<b>{penyakit_map[disease]['name']}</b>:<ul><li>Pengertian : {penyakit_map[disease]['definition']}</li><li> Teraphy : {penyakit_map[disease]['teraphy']}</li></ul>" for disease in matched_diseases]
            result = f"Diagnosis result: \n <ol>{', '.join(match_disease)}"
            
            result =  result.replace('\n', '<br />')
        else:
            possible_diseases = set()
            for symptom in selected_symptoms:
                for disease_code, disease_info in penyakit_map.items():
                    if symptom in disease_info['symptoms']:
                        possible_diseases.add(disease_code)

            if possible_diseases:
                disease_names = [f"<li><b> {penyakit_map[disease]['name']}</b>: <ul><li>Pengertian : {penyakit_map[disease]['definition']}</li><li>Teraphy : {penyakit_map[disease]['teraphy']}</li></ul> </li>" for disease in possible_diseases]
                result = f"Tidak ada gejala yang sesuai. Namun, ditemukan kemungkinan diagnosis : \n <ol> {' '.join(disease_names)}"
            else:
                result = "Tidak ada gejala yang sesuai dengan pilihan Anda. Dibutuhan spesifikasi gejala untuk menemukan hasil diagnosis"

            result =  result.replace('\n', '<br />')

        return render_template('result_stroke_diagnosis.html', result=result)
    
    return render_template('result_stroke_diagnosis.html')

@app.route('/prediksi')
def prediksi():
    return render_template('prediksi.html')

def ValuePredictorMortalitas(to_predict_list):
    to_predict = np.array(to_predict_list).reshape(1, 17)
    loaded_model = joblib.load('model_xgb_best_mortalitas.joblib')
    result = loaded_model.predict(to_predict)
    return result[0]

def ValuePredictorRawatInap(to_predict_list):
    to_predict = np.array(to_predict_list).reshape(1, 17)
    loaded_model = joblib.load('model_xgb_best_rawat.joblib')
    result = loaded_model.predict(to_predict)
    return result[0]
 
@app.route('/result', methods = ['POST'])
def result():
    if request.method == 'POST':
        to_predict_list = request.form.to_dict()
        to_predict_list = list(to_predict_list.values())
        to_predict_list = list(map(float, to_predict_list))
        resultMortalitas = ValuePredictorMortalitas(to_predict_list)
    
        if int(resultMortalitas) == 1:
            prediction_label_mortalitas ='Pasien Berpotensi Meninggal / The patient has the potentional to die'
        else:
            prediction_label_mortalitas ='Pasien Berpotensi Sembuh / Patients with potential recovery'  

        return render_template("result.html", predictionMortalitas = prediction_label_mortalitas )

@app.route('/result_lama_rawat_inap', methods = ['POST'])
def result_lama_rawat_inap():
    if request.method == 'POST':
        to_predict_list = request.form.to_dict()
        to_predict_list = list(to_predict_list.values())
        to_predict_list = list(map(float, to_predict_list))
        resultRawatInap = ValuePredictorRawatInap(to_predict_list)
        
        if int(resultRawatInap) == 1:
            prediction_label_rawat_inap ='Lebih Dari 7 Hari (Tidak Standar) / More than 7 days (Non-standard)'
        else:
            prediction_label_rawat_inap ='Kurang dari sama dengan 7 Hari (Standar) / Less than equal to 7 Days (Standard)' 

        return render_template("result_lama_rawat_inap.html", predictionRawatInap = prediction_label_rawat_inap )

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('username', None)
    session.pop('level', None)
    return redirect(url_for('login'))

#if __name__ == '__main__':
    #app.run(debug=True)

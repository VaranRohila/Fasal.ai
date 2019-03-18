from flask import *
import pandas as pd
import numpy as np
import urllib, json
from sklearn.externals import joblib
#from flask_static_compress import FlaskStaticCompress



def get_temp(city):  
    url = "http://api.openweathermap.org/data/2.5/forecast?q="+str(city)+",in&appid=b396b019f0bd0eb648c68231d7147fea"
    response = urllib.request.Request(url)
    opener = urllib.request.build_opener()
    f = opener.open(response)
    json1 = json.loads(f.read())
    temp = 0
    temp_c = []
    for i in range(len(json1['list'])):
        temp += (json1['list'][i]['main']['temp_min']+json1['list'][i]['main']['temp_max'])/2
        if ((i+1)%8)==0 and i>0:
            temp /= 8
            temp_c.append(temp-273.15)
            temp = 0
    return temp_c
app = Flask(__name__)

app.config['COMPRESSOR_DEBUG'] = app.config.get('DEBUG')
app.config['COMPRESSOR_STATIC_PREFIX'] = 'static'
app.config['COMPRESSOR_OUTPUT_DIR'] = 'build'
app.static_folder = 'static' 
#compress = FlaskStaticCompress(app)

trop = {0 : 'Cotton', 1 : 'Jute', 2: 'Rice', 3: 'Sorghum', 4: 'Sugarcane', 5: 'Wheat'}
area = 0
@app.route('/')
def index():
    states = {
        'West Bengal': ['Alipurduar', 'Bankura','Bardhaman','Birbhum','Coochbehar','Darjeeling','Dinajpur Dakshin','Dinajpur Uttar','Hooghly','Howrah','Jalpaiguri','Maldah','Medinipur East','Medinipur West','Murshidabad','Nadia','Purulia'],
        'Gujarat': ['Ahmadabad','Amreli','Anand','Aravalli','Banas Kantha','Bharuch','Bhavnagar','Botad','Chhotaudepur','Dahod','Dang','Devbhumidwarka','Gandhinagar','Girsomnath','Jamnagar','Junagadh','Kachchh','Kheda','Mahesana','Mahisagar','Morbi','Narmada','Navsari','Panch Mahals','Patan','Porbandar','Rajkot','Sabar Kantha','Surat','Surendranagar','Tapi','Vadodara','Valsad'],
        'Maharashtra': ['Ahmednagar','Akola','Amravati','Aurangabad','Beed','Bhandara','Buldhana','Chandrapur','Dhule','Gadchiroli','Gondia','Hingoli','Jalgaon','Jalna','Kolhapur','Latur','Nagpur','Nanded','Nandurbar','Nashik','Osmanabad','Palghar','Parbhani','Pune','Raigad','Ratnagiri','Sangli','Satara','Sindhudurg','Solapur','Thane','Wardha','Washim','Yavatmal'],
        'Uttar Pradesh': ['Agra','Aligarh','Allahabad','Ambedkar Nagar','Amethi','Amroha','Auraiya','Azamgarh','Baghpat','Bahraich','Ballia','Balrampur','Banda','Barabanki','Bareilly','Basti','Bijnor','Budaun','Bulandshahr','Chandauli','Chitrakoot','Deoria','Etah','Etawah','Faizabad','Farrukhabad','Fatehpur','Firozabad','Gautam Buddha Nagar','Ghaziabad','Ghazipur','Gonda','Gorakhpur','Hamirpur','Hapur','Hardoi','Hathras','Jalaun','Jaunpur','Jhansi','Kanpur Dehat','Kannauj','Kanpur Nagar','Kasganj','Kaushambi','Kheri','Khushi Nagar','Lalitpur','Lucknow','Maharajganj','Mahoba','Mainpuri','Mathura','Meerut','Mau','Mirzapur','Moradabad','Muzaffarnagar','Pilibhit','Pratapgarh','Rae Bareli','Rampur''Saharanpur','Sambhal','Sant Kabeer Nagar','Sant Ravidas Nagar','Shahjahanpur','Shamli','Shravasti','Siddharth Nagar','Sitapur','Sonbhadra','Sultanpur','Unnao','Varanasi']
    }

    return render_template('home.html', states=states)

@app.route('/login',methods = ['POST', 'GET'])
def login():
   state = request.form.get('state')
   city = request.form.get('city')
   area = request.form.get('area')
   #pH 
   pH = pd.read_csv('./pH.csv')
   pH.set_index('district_name', inplace= True)
   potent = pH.loc[city, 'pH']

   #  Temperature
   temp = get_temp(city)
   print(temp)



   #Rainfall
   dictionary = {'Maharashtra' : './pred_mh.csv', 'Uttar Pradesh': './pred_up.csv', 'Gujarat': './pred_gj.csv', 'West Bengal': './pred_wb.csv'}
   rain = pd.read_csv(dictionary[state])
   rain = rain.iloc[0, 1]

   #model
   #data = [potent,rain,temp]
   data = {'ph': [potent], 'rainfall': [rain], 'temp': [np.array(temp).mean()]}
   print(data)
   o = pd.DataFrame(data = data)
   #xg = xgb.DMatrix(data)
   model = joblib.load("xg_new_clf.pkl")
   prediction = np.array(model.predict_proba(o))
   prediction = np.argsort(-prediction)[:3]
   crop_1 = trop[prediction[0][0]]
   crop_2 = trop[prediction[0][1]]
   crop_3 = trop[prediction[0][2]]
   #prediction = crop[prediction[0]]
   #print(prediction)


   return render_template('crop.html', crop_1 = crop_1, crop_2 = crop_2, crop_3 = crop_3, area = area) # just to see what select is

@app.route('/crop/<name>/<area>')
def crop(name, area):
   msp = pd.read_csv('./msp.csv')
   msp.set_index('Crop', inplace = True)
   price = msp.loc[name]['19']
   s_price = pd.read_csv('./seed_prices.csv')
   s_price.set_index('Type', inplace = True)
   total_seed_price = s_price.loc[name, 'costperkg'] * s_price.loc[name, 'seedrate'] * float(area) 

   return render_template('crop_depth.html', crop = name, msp = price, seed_price = total_seed_price)
if __name__ == '__main__':
   app.run(debug = True)
import os

from flask import Flask, request, render_template, send_from_directory
import requests


# Replace 'KEY_1' with your subscription key as a string


def getImageData(filename):
    subscription_key = 'bf07f7fd487d45f09e72bc6ccbcf3265'

    uri_base = 'https://eastus.api.cognitive.microsoft.com'

    headers = {
        'Content-Type': 'application/octet-stream',
        'Ocp-Apim-Subscription-Key': subscription_key,
    }

    params = {
        'returnFaceId': 'true',
        'returnFaceAttributes': 'age,smile,headPose,emotion,blur,exposure,noise',
    }

    path_to_face_api = '/face/v1.0/detect'

    with open(filename, 'rb') as f:
        img_data = f.read()
    try:

        response = requests.post(uri_base + path_to_face_api,
                                 data=img_data,
                                 headers=headers,
                                 params=params)

        # print ('Response:')
        # json() is a method from the request library that converts
        # the json reponse to a python friendly data structure
        parsed = response.json()

        # display the image analysis data
        return (parsed)


    except Exception as e:
        # print('Error:')
        return (e)


def takeSecond(elem):
    return elem[1]


def sortFaces(arr):
    new_arr = sorted(arr, key=takeSecond)
    out = []

    for element in new_arr:
        out.append(element[0])

    return out


def getScore(imageDict):
    score_arr = []
    for person in imageDict:
        attributes = person
        faceId = attributes["faceId"]

        faceLeft = attributes["faceRectangle"]["left"]
        faceSmile = attributes["faceAttributes"]["smile"]
        faceTilt = attributes["faceAttributes"]["headPose"]["roll"]
        faceHappiness = attributes["faceAttributes"]["emotion"]["happiness"]
        faceBlurLevel = attributes["faceAttributes"]["blur"]["blurLevel"]
        faceBlurLevelValue = attributes["faceAttributes"]["blur"]["value"]
        faceExposureLevel = attributes["faceAttributes"]["exposure"]["exposureLevel"]
        faceExposureLevelValue = attributes["faceAttributes"]["exposure"]["value"]
        faceNoiseLevelValue = attributes["faceAttributes"]["noise"]["value"]

        score = 0

        if faceSmile == 1.0:
            score += 50
        else:
            score += 25

        score -= abs(faceTilt)

        score += faceHappiness * 15

        score -= faceBlurLevelValue * 75

        if faceExposureLevel == "goodExposure":
            score += faceExposureLevelValue * 50

        elif faceExposureLevel == "underExposure" or faceExposureLevel == "overExposure":
            score -= faceExposureLevelValue * 25

        score -= faceNoiseLevelValue * 10

        score_arr.append((round(score), faceLeft))

    return sortFaces(score_arr)




app = Flask(__name__)

APP_ROOT = os.path.dirname(os.path.abspath(__file__))





@app.route('/')
def index():
    return render_template('upload.html')


@app.route("/upload", methods=["POST"])
def upload():
    target = os.path.join(APP_ROOT, 'images/')
    print(target)
    if not os.path.isdir(target):
            os.mkdir(target)
    else:
        print("Couldn't create upload directory: {}".format(target))
    print(request.files.getlist("file"))

    files = []
    scores = []

    photo_number = request.form["photo_number"]

    for upload in request.files.getlist("file"):
        print(upload)
        print("{} is the file name".format(upload.filename))
        filename = upload.filename
        destination = "/".join([target, filename])
        print ("Accept incoming file:", filename)
        print ("Save it to:", destination)

        upload.save(destination)
        files.append(filename)
        scores.append(getScore(getImageData(destination)))

    images = []
    count = 0
    outStr = ""

    for file in files:
        images.append((file, scores[count]))

        outStr += "< img src = \" {{url_for('send_image', filename="+file+")}}\" >"
        outStr += "<p>"+ str(scores[count]) + "</p><br>"
        count += 1

    '''
    Variable Information -
    
    images = [("profpic.png", [73]), ("travis.jpg", [45])]
    
    
    '''


    # return send_from_directory("images", filename, as_attachment=True)
    return render_template("complete.html", files=files, scores=scores, numberSpecified=photo_number)


@app.route('/upload/<filename>')
def send_image(filename):
    return send_from_directory("images", filename)

@app.route('/gallery')
def get_gallery():
    image_names = os.listdir('./images')
    print(image_names)
    return render_template("gallery.html", image_names=image_names)




if __name__ == '__main__':
    app.run()

#import matplotlib.pyplot as plt
import torch
import torch.nn as nn
import numpy as np
import os
from args import get_parser
import pickle
from model import get_model
from torchvision import transforms
from utils.output_utils import prepare_output
from PIL import Image
import time
from tensorflow.keras.models import load_model
import tensorflow.keras.backend as K
from tensorflow.keras.preprocessing import image
import pandas as pd
from flask import Flask, request, abort, jsonify
from  flask_cors import CORS

app = Flask(__name__)
CORS(app)

requestFolderName = 'demo_images'
receipeModel = None
model_best = None

import os
os.environ['KMP_DUPLICATE_LIB_OK']='True'

data_dir = 'models/'
# code will run in gpu if available and if the flag is set to True, else it will run on cpu
use_gpu = False
device = torch.device('cuda' if torch.cuda.is_available() and use_gpu else 'cpu')
map_loc = None if torch.cuda.is_available() and use_gpu else 'cpu'





def food_classification():
    # Loading the best saved model to make predictions
    K.clear_session()
    model_path = os.path.join(data_dir, 'best_model_3class.hdf5')
    model_best = load_model(model_path, compile=False)
    return model_best

food_list = ['ice_cream','ramen','pad_thai','fried_rice','chicken_curry','hot_and_sour_soup','french_onion_soup']

def predict_class(model, img, show = False):

    img = image.load_img(img, target_size=(299, 299))
    img = image.img_to_array(img)
    img = np.expand_dims(img, axis=0)
    img /= 255.

    pred = model.predict(img)
    index = np.argmax(pred)
    food_list.sort()
    pred_value = food_list[index]
    return pred_value


"""
Receipe Gen code
"""
def loadReceipeModel():
    ingrs_vocab = pickle.load(open(os.path.join(data_dir, 'ingr_vocab.pkl'), 'rb'))
    vocab = pickle.load(open(os.path.join(data_dir, 'instr_vocab.pkl'), 'rb'))
    title = ''
    ingr_vocab_size = len(ingrs_vocab)
    instrs_vocab_size = len(vocab)
    output_dim = instrs_vocab_size
    t = time.time()
    import sys;
    sys.argv = [''];
    del sys
    args = get_parser()
    args.maxseqlen = 15
    args.ingrs_only = False
    model = get_model(args, ingr_vocab_size, instrs_vocab_size)
    # Load the trained model parameters
    model_path = os.path.join(data_dir, 'modelbest.ckpt')
    model.load_state_dict(torch.load(model_path, map_location=map_loc))
    model.to(device)
    model.eval()
    model.ingrs_only = False
    model.recipe_only = False
    print('loaded model')
    print("Elapsed time:", time.time() - t)
    return model

def getReceipe(img_file,receipeModel):

    transf_list_batch = []
    transf_list_batch.append(transforms.ToTensor())
    transf_list_batch.append(transforms.Normalize((0.485, 0.456, 0.406),
                                                  (0.229, 0.224, 0.225)))
    to_input_transf = transforms.Compose(transf_list_batch)
    #greedy = [True, False, False, False]
    greedy = [True]
    beam = [-1, -1, -1, -1]
    temperature = 1.0
    numgens = len(greedy)

    image_path = img_file
    image = Image.open(image_path).convert('RGB')

    transf_list = []
    transf_list.append(transforms.Resize(256))
    transf_list.append(transforms.CenterCrop(224))
    transform = transforms.Compose(transf_list)

    image_transf = transform(image)
    image_tensor = to_input_transf(image_transf).unsqueeze(0).to(device)

    #plt.imshow(image_transf)
    # plt.axis('off')
    # plt.show()
    # plt.close()

    num_valid = 1
    for i in range(numgens):
        with torch.no_grad():
            outputs = receipeModel.sample(image_tensor, greedy=greedy[i],
                                   temperature=temperature, beam=beam[i], true_ingrs=None)

        ingr_ids = outputs['ingr_ids'].cpu().numpy()
        recipe_ids = outputs['recipe_ids'].cpu().numpy()
        ingrs_vocab = pickle.load(open(os.path.join(data_dir, 'ingr_vocab.pkl'), 'rb'))
        vocab = pickle.load(open(os.path.join(data_dir, 'instr_vocab.pkl'), 'rb'))


        outs, valid = prepare_output(recipe_ids[0], ingr_ids[0], ingrs_vocab, vocab)
        print('-----------------')
        print(outs)
        print('-----------------')
        return outs;
    return ""
        # show_anyways = False
        # if valid['is_valid'] or show_anyways:
        #
        #     print('RECIPE', num_valid)
        #     num_valid += 1
        #     # print ("greedy:", greedy[i], "beam:", beam[i])
        #
        #     BOLD = '\033[1m'
        #     END = '\033[0m'
        #     title = outs['title']
        #     print(BOLD + '\nTitle:' + END, outs['title'])
        #
        #     print(BOLD + '\nIngredients:' + END)
        #     print(', '.join(outs['ingrs']))
        #
        #     print(BOLD + '\nInstructions:' + END)
        #     print('-' + '\n-'.join(outs['recipe']))
        #
        #     print('=' * 20)
        #     print('Calorie Information : ',getCalorieInformation(outs['title']));
        #     print('*' * 20)
        #
        #
        #
        # else:
        #     pass
        #     print("Not a valid recipe!")
        #     print("Reason: ", valid['reason'])

def getCalorieInformation(title):
    df = pd.read_csv(data_dir+'/nutrition.csv',low_memory=False);
    nutrients = df[df['title']==title]['nutr_values_per100g'].tolist()
    return nutrients

@app.route('/test')
def test():
    return 'Hello'


@app.route('/seefood',methods=["POST"])
def seeFood():
    fileimage = request.files['file']
    count = len(os.listdir(requestFolderName)) + 1
    img_file = os.path.join(requestFolderName, 'image-'+str(count)+'.jpg')
    fileimage.save(img_file)

    startTime = time.time()
    # predict_class(model_best, images, True)
    #img_file = 'images/ibg-endings-icecream-fried.jpg'
    receipeModel = loadReceipeModel()

    outs = getReceipe(img_file, receipeModel)
    model_best = food_classification()
    print('model_best ', model_best)
    img = image.load_img(img_file, target_size=(299, 299))
    print('image shape: ', img)
    pred_value = predict_class(model_best, img_file, False)
    print('pred_value ', pred_value)
    print('Total time taken : ', time.time() - startTime)
    output = {}
    output['classification'] = pred_value
    output['receipe'] = outs
    output['calorie'] = getCalorieInformation(outs['title'])

    return output


if __name__=='__main__':
    print('hello')
    app.run(host= 'localhost',port= '5001',debug=True)

    #


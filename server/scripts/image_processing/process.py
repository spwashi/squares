import os
import cv2
import numpy as np
from matplotlib import pyplot as plt

current_directory = os.path.dirname(os.path.realpath(__file__))

scale = ["percentage", "fixed", "pass"][2]
nocheck = True


def process_image(file_name, do_show=False, output_dir=current_directory + '/out'):
    img_in = cv2.imread(file_name)
    img_in = cv2.rotate(img_in, cv2.ROTATE_180)

    if scale == "percentage":
        dim = scale_img_dimensions(img_in)
    elif scale == "fixed":
        dim = scale_img_fixed(img_in)
    else:
        dim = scale_img_pass(img_in)


    orig = cv2.resize(img_in, dim, interpolation=cv2.INTER_AREA)
    img_in = orig.copy()
    img_out = orig.copy()

    evaluations = evaluate_image(img_in)

    contours, hierarchy = cv2.findContours(evaluations["morph"], cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    images = process_contours(contours, orig, img_out, output_dir)

    if not do_show:
        return images

    plot_and_wait(evaluations, orig, img_out)


def process_contours(contours, img_orig, img_out, dir_img):
    cv2.drawContours(image=img_out, contours=contours, contourIdx=-1,
                     color=(0, 255, 0), thickness=2, lineType=cv2.LINE_AA)
    min_area = 100
    max_area = 150000
    image_number = 0
    images = []
    # contours = contours[0] if len(contours) == 2 else contours[1]
    for c in contours:
        area = cv2.contourArea(c)
        print(area, min_area < area < max_area)
        if nocheck or (min_area < area < max_area):
            x, y, w, h = cv2.boundingRect(c)
            roi = img_orig[y:y + h, x:x + w]
            try:
                os.mkdir(dir_img)
            except FileExistsError:
                pass
            img_name = '/ROI_{}.png'.format(image_number)
            cv2.imwrite(dir_img + img_name, roi)
            cv2.rectangle(img_out, (x, y), (x + w, y + h), (36, 255, 12), 2)
            image_number += 1
            images.append(img_name)
    return images


def plot_and_wait(evaluations, orig, out):
    plt.figure(figsize=(10, 10))
    titles = {
        'Original Image':      orig,
        'BINARY':              evaluations["binary"],
        'BINARY_INV':          evaluations["binary_inverted"],
        'TRUNC':               evaluations["trunc"],
        'TOZERO':              evaluations["tozero"],
        'TOZERO_INV':          evaluations["tozero_inv"],
        'Adaptive Mean':       evaluations["th_adaptive_mean"],
        'Adaptive Gaussian':   evaluations["th_adaptive_gaussian"],
        "Otsu's Thresholding": evaluations["otsu"],
        "Morphology":          evaluations["morph"],
        "Highlighted":         out
    }
    i = 0
    for key in titles:
        i += 1
        plt.subplot(2, 2, i), plt.imshow(titles[key], 'gray')
        try:
            plt.title(key)
        except IndexError:
            plt.title('something')
        plt.xticks([]), plt.yticks([])
    plt.show()
    cv2.destroyAllWindows()
    # cv2.imshow('sharpened', sharpened)
    # cv2.waitKey(0)


def evaluate_image(img):
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = cv2.medianBlur(img, 11)
    kernel = np.array([
        [0, -1, 0],
        [-1, 5, -1],
        [0, -1, 0]
    ])
    img = cv2.filter2D(img, -1, kernel)
    ret, binary = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)
    ret, binary_inverted = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)
    ret, trunc = cv2.threshold(img, 127, 255, cv2.THRESH_TRUNC)
    ret, tozero = cv2.threshold(img, 127, 255, cv2.THRESH_TOZERO)
    ret, tozero_inv = cv2.threshold(img, 127, 255, cv2.THRESH_TOZERO_INV)
    th_adaptive_mean = cv2.adaptiveThreshold(
        img, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2)
    th_adaptive_gaussian = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    blur = cv2.GaussianBlur(img, (5, 5), 0)
    ret3, otsu = cv2.threshold(
        blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    otsu1 = cv2.morphologyEx(otsu, cv2.MORPH_CLOSE, kernel, iterations=10)
    morph = cv2.morphologyEx(otsu1, cv2.MORPH_OPEN, kernel, iterations=10)
    return {
        'binary':               binary,
        'binary_inverted':      binary_inverted,
        'morph':                morph,
        'otsu':                 otsu,
        'th_adaptive_gaussian': th_adaptive_gaussian,
        'th_adaptive_mean':     th_adaptive_mean,
        'tozero':               tozero,
        'tozero_inv':           tozero_inv,
        'trunc':                trunc
    }


def scale_img_pass(img):
    return img.shape[0], img.shape[1]


def scale_img_fixed(img):
    width = 900
    height = int((width / img.shape[1]) * img.shape[1])
    return width, height


def scale_img_dimensions(img):
    scale_percent = 10
    width = int(img.shape[1] * scale_percent / 100)
    height = int(img.shape[0] * scale_percent / 100)
    return width, height

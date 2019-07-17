import cv2
import numpy as np

from PIL import Image # required for opencv, just not openly
from re import sub


# Credit to Django text utils https://github.com/django/django/blob/master/django/utils/text.py
def get_valid_filename(s):
    s = str(s).strip().replace(' ', '_')
    return sub(r'(?u)[^-\w.]', '', s)


def resize_image(image, dimensions, filename, filetype="png"):
    try:
        width = int(dimensions[0])  # dimensions[2] contains channel information, but is ignored by default
        height = int(dimensions[1])
    except IndexError:
        raise ValueError("[ERROR] 'dimensions' in resize_image should be a tuple of integers.")
    except ValueError:
        raise ValueError("[ERROR] Non-numerical height or width value detected.")
    if height < 1:
        raise ValueError("[ERROR] Non-positive height detected. That image wouldn't be much good.")
    if width < 1:
        raise ValueError("[ERROR] Non-positive width detected. That image wouldn't be much good.")

    if (width, height) != image.shape[:-1]:  # sometimes this function is called for conversion and naming, not resizing | [:-1] clips the (width, height, channels) tuple to just (width, height)
        ret = cv2.resize(image, (width, height))
    else:
        ret = image

    save_filename = "images/" + get_valid_filename(filename) + "_{}x{}.{}".format(width, height, filetype)
    cv2.imwrite(save_filename, ret)

    return save_filename


async def fetch_and_resize_image(session, url, filename, dimensions=None): # WORKS but slow for inexplicable reasons
    async with session.get(url) as image_response:
        if image_response.status == 200:
            image_array = np.asarray(bytearray(await image_response.read()), dtype="uint8") # create a numpy array from the byte array we get from reading the stream, where the data in the array is uint8's
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR) #BREAKABLE

            if not dimensions: # if we werent told to resize the image:
                dimensions = image.shape # use the filetype and naming convention of resize_image without actually resizing
            image = resize_image(image, dimensions, filename, filetype="jpeg") # get the last part (image name) of the url
            return image, dimensions # (file path to image, dimensions) tuple

        else:
            raise Exception("[WARNING] (HTTP Code {}) Image fetching failed from the following URL: {}".format(image_response.status, url))
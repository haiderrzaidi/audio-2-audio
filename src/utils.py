"""Reuseable general utilities functions to be used application wide
"""

import numpy as np  # type: ignore
import os
from PIL import Image
from datetime import datetime, timedelta
import pickle as pkl
import base64
from io import BytesIO
import PIL
import requests
import traceback
import time
import logging
import sys
import string

ROOT = __file__
user_agent = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1)"
    "AppleWebKit/602.2.14 (KHTML, like Gecko) Version/10.0.1 Safari/602.2.14"
)
headers = {"User-Agent": user_agent}


def get_logger(name, level=logging.INFO):
    c_handler = logging.StreamHandler()
    c_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    c_handler.setFormatter(c_format)
    logger_ = logging.getLogger(name)
    logger_.addHandler(c_handler)
    logger_.setLevel(level)
    logger_.propagate = False
    return logger_


logger = get_logger("Utils")


def write_to_file(obj, directory, filename):
    """write a object to file on disk as pickle
    Args:
        obj:
        directory:
        filename:

    Returns:

    """
    filepath = os.path.join(directory, filename)

    with open(filepath, "wb") as f:
        pkl.dump(obj, f)


def read_from_file(filepath: str):
    """reads a object from a pickle file on disk
    Args:
        filepath: the full file path to the pickle file


    Returns:
        object: returns an object from the pickle file

    """
    with open(filepath, "rb") as f:
        obj = pkl.load(f)
    return obj


def load_image(path):
    """loads an image using PIL

    Args:
        path(str):

    Returns:
        PIL.Image.Image

    """
    img = Image.open(path)
    return img


def preprocess_image(img, image_size):
    """preprocesses the image applying different operation

    Args:
        img(PIL.Image.Image):
        image_size(list[iny]): image size of format [IMAGE_WIDTH, IMAGE_HEIGHT]

    Returns:
        np.ndarray: return the numpy array representation of the image

    """

    img = img.resize(image_size)
    imgarr = np.asarray(img)
    imgarr = imgarr.astype("float32")

    return imgarr


def generate_batches(nexamples, batch_size):
    """generates a list of tuples of starts and ends of size nbatches

    Args:
        nexamples(int):
        batch_size(int):

    Returns:
        list: a list of tuples with start and end index of each batch

    """

    nbatches = int(np.ceil(nexamples / batch_size))
    batches = []
    for batch in range(nbatches):
        start = batch * batch_size
        end = start + batch_size

        if end > nexamples:
            end = nexamples

        batches.append((start, end))

    return batches


def get_datetime():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def divisor_generator(n):
    large_divisors = []
    for i in range(1, int(np.sqrt(n) + 1)):
        if n % i == 0:
            yield i
            if i * i != n:
                large_divisors.append(int(n / i))
    for divisor in reversed(large_divisors):
        yield divisor


def get_batch_size(nexamples, selected_batch_size, lower_bound=True):
    """return the batchsize which is exactly divisible by the number
    of examples an is closest to the proposed batchsize

    Args:
        nexamples(int):
        selected_batch_size(int):
        lower_bound(bool):

    Returns:
        int: a closet divisible batchsize

    """

    divisors = list(divisor_generator(nexamples))[1:-1]

    if len(divisors) == 0:
        if lower_bound is True:
            return 1
        else:
            return nexamples

    previous_divisor = divisors[0]
    for divisor in divisors:
        if selected_batch_size < divisor:
            if lower_bound is True:
                return previous_divisor
            else:
                return divisor
        previous_divisor = divisor


def string_to_base64(buff: str):
    """convert a string to base64 number

    Args:
        string(str):  a string to be encoded to base64

    Returns:
        str: a base64 string

    """

    b = buff.encode("utf-8")
    encoded_byts = base64.b64encode(b)
    encoded_string = encoded_byts.decode("utf-8")
    return encoded_string


def bytes_to_base64(byts):
    """convert a string to base64 number

    Args:
        string(str):  a string to be encoded to base64

    Returns:
        str: a base64 string

    """
    encoded_string = base64.b64encode(byts)
    encoded_string = encoded_string.decode("utf-8")
    return encoded_string


def base64_to_string(base64string):
    """decode  a base64 byte string

    Args:
        base64string(str): base64 byte string

    Returns:
        str: the original string

    """
    s = base64.b64decode(base64string)
    s = s.decode("utf-8")
    return s


def base64_to_bytes(base64string):
    """decode  a base64 byte string

    Args:
        base64string(str): base64 byte string

    Returns:
        bytes: the original byte content

    """
    s = base64.b64decode(base64string)
    return s


def base64_to_imagearray(base64string, image_size):
    """converts the base 64 image string to numpy array

    Args:
        base64string(str):
        image_size(list[int]): image size of format [IMAGE_WIDTH, IMAGE_HEIGHT].
            image is not resize if None is provided

    Returns:

    """
    string_image = base64_to_bytes(base64string)
    buffered2 = BytesIO(string_image)
    img2 = Image.open(buffered2)
    if image_size is not None:
        img2 = img2.resize(image_size)
    img2_array = np.asarray(img2)
    return img2_array


def image_to_base64(imagepath, image_size, image_format="PNG"):
    """reads image from a filepath or file object and converts it into base64

    Args:
        imagepath:
        image_size(list[int]): image size of format [IMAGE_WIDTH, IMAGE_HEIGHT]

    Returns:

    """
    img = Image.open(imagepath)
    img = img.resize(image_size, resample=PIL.Image.ANTIALIAS)
    buffered = BytesIO()
    img.save(buffered, format=image_format)
    imgstr = buffered.getvalue()
    base64_image = bytes_to_base64(imgstr)

    return base64_image


def urlimage_to_base64(url, image_size, timeout=10):
    """fetches image from a url and converts it to base64.
    Args:
        timeout (int): time in seconds
        url(str):
        image_size(list[int]): image size of format [IMAGE_WIDTH, IMAGE_HEIGHT]

    Returns:
        str: base64 string. returns None of an error occurred while fetching

    """
    try:
        response = requests.get(url, timeout=timeout, headers=headers)
        img_bytes_io = BytesIO(response.content)
        img_base64 = image_to_base64(img_bytes_io, image_size)
        return img_base64
    except Exception as ex:  # pylint: disable=broad-except
        msg = str(ex)
        logger.error(f"Error while fetching {url}: {msg}")
        logger.exception(ex)
        return None


def post(
    url: str,
    data: dict,
    headers_: dict[str, str] | None = None,
    max_retry: int = 0,
    wait: int = 2,
    json: bool = True,
    debug: bool = False,
    timeout: timedelta = timedelta(seconds=10),
):
    retry = 0
    while retry <= max_retry:
        try:
            response = None
            if json is True:
                response = requests.post(
                    url, headers=headers_, json=data, timeout=timeout.total_seconds()
                )
            else:
                response = requests.post(
                    url, headers=headers_, data=data, timeout=timeout.total_seconds()
                )

            code = response.status_code
            response_text = response.text
            if code != 200:
                raise RuntimeError(response_text)

            return response_text
        except Exception as e:  # pylint: disable=broad-except
            msg = str(e)
            msg = msg if len(msg) < 200 else msg[:200]
            st = traceback.format_exc()
            print(msg)
            if debug is True:
                print(st)

        time.sleep(wait)
        retry += 1
    raise RuntimeError("failed to complete request in the given retries")


def get(
    url,
    data=None,
    headers_: dict[str, str] | None = None,
    max_retry: int = 3,
    wait: int = 2,
    debug: bool = False,
    timeout: timedelta = timedelta(seconds=10),
):
    retry = 1
    while retry <= max_retry:
        try:
            response = None
            response = requests.get(
                url, params=data, timeout=timeout.total_seconds(), headers=headers_
            )
            code = response.status_code
            response_text = response.text
            if code != 200:
                raise RuntimeError(response_text)

            return response_text
        except Exception as e:  # pylint: disable=broad-except
            msg = str(e)
            msg = msg if len(msg) < 200 else msg[:200]
            st = traceback.format_exc()
            logger.error(msg)
            if debug is True:
                print(st)

        time.sleep(wait)
        retry += 1
    raise RuntimeError("failed to complete request in the given retries")


def generate_randomstring():
    digits = "".join(
        [str(np.random.choice(list(string.digits), 1)[0]) for i in range(8)]
    )
    chars = "".join(
        [str(np.random.choice(list(string.ascii_letters), 1)[0]) for i in range(15)]
    )
    val = digits + chars
    return val


def api_extract_test(json_request):
    """extracts the test from api json request

    Args:
        json_request(dict):

    Returns:

    """

    if not isinstance(json_request, dict):
        raise ValueError("json body must be a dictionary")
    test = json_request.get("test", [])

    if len(test) == 0:
        raise ValueError("test cannot be empty")

    return test


def api_convert_base64_images(
    b64_images,
    image_size: tuple[int, int] = (
        128,
        128,
    ),
):
    """converts a list of base64 images to json
    compliant list of images

    Args:
        data(list[str]): list of base64 images

    Returns:
        list: returns a list of images of dimention
            image_width, image_height, channels


    """

    try:
        images = [base64_to_imagearray(i, image_size) for i in b64_images]

    except Exception as ex:
        raise ValueError("base64 decode error") from ex

    return images


def get_full_path(*paths):
    root_dir = os.path.dirname(ROOT)
    full_path = os.path.join(root_dir, *paths)
    return full_path


def format_exception(exception_msg):
    """formats the exception message. include details such as line no and filename

    Returns:
        str: returns the formatted exception
    """
    exc_type, _, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    lineno = str(exc_tb.tb_lineno)
    exc_type = str(exc_type)
    msg = f"{exc_type} {fname}:{lineno} {exception_msg}"
    return msg

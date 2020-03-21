# -*- coding: utf-8 -*-
import os
import cv2
import copy
import numpy as np
from tqdm import tqdm
from urllib.request import urlretrieve


class TqdmUpTo(tqdm):
    """
    Provides `update_to(n)` which uses `tqdm.update(delta_n)`.
    https://pypi.org/project/tqdm/#hooks-and-callbacks
    """
    def update_to(self, b=1, bsize=1, tsize=None):
        """
        b  : int, optional
            Number of blocks transferred so far [default: 1].
        bsize  : int, optional
            Size of each block (in tqdm units) [default: 1].
        tsize  : int, optional
            Total size (in tqdm units). If [default: None] remains unchanged.
        """
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)  # will also set self.n = b * bsize


def download(url: str, save_dir: str):
    """
    Downloads file by http request, shows remaining time.
    https://pypi.org/project/tqdm/#hooks-and-callbacks
    Example inputs:
        url: 'ftp://smartengines.com/midv-500/dataset/01_alb_id.zip'
        save_dir: 'data/'
    """

    # create save_dir if not present
    create_dir(save_dir)
    # download file
    with TqdmUpTo(unit='B', unit_scale=True, miniters=1,
                  desc=url.split('/')[-1]) as t:  # all optional kwargs
        urlretrieve(url, filename=os.path.join(save_dir, url.split('/')[-1]),
                    reporthook=t.update_to, data=None)


def create_dir(_dir):
    """
    Creates given directory if it is not present.
    """
    if not os.path.exists(_dir):
        os.makedirs(_dir)


def get_files(img_dir):
    imgs, masks, xmls = list_files(img_dir)
    return imgs, masks, xmls


def list_files(in_path):
    img_files = []
    mask_files = []
    gt_files = []
    for (dirpath, dirnames, filenames) in os.walk(in_path):
        for file in filenames:
            filename, ext = os.path.splitext(file)
            ext = str.lower(ext)
            if (ext == '.jpg' or ext == '.jpeg' or ext == '.gif' or
                    ext == '.png' or ext == '.pgm'):
                img_files.append(os.path.join(dirpath, file))
            elif ext == '.bmp':
                mask_files.append(os.path.join(dirpath, file))
            elif ext == '.xml' or ext == '.gt' or ext == '.txt':
                gt_files.append(os.path.join(dirpath, file))
            elif ext == '.zip':
                continue
    # img_files.sort()
    # mask_files.sort()
    # gt_files.sort()
    return img_files, mask_files, gt_files


def export_detected_region(image, points, file_path, smooth_contour=False):
    """
    Arguments:
        image: full image
        points: bbox or poly points
        file_path: path to be exported
        smooth_contour: if true, curved/smoothed region will be cropped
    """
    # points should have 1*4*2  shape
    if len(points.shape) == 2:
        points = np.array([np.array(points).astype(np.int32)])

    # create mask with shape of image
    mask = np.zeros(image.shape[0:2], dtype=np.uint8)

    if smooth_contour:
        # method 1 smooth region
        cv2.drawContours(mask, [points], -1, (255, 255, 255), -1, cv2.LINE_AA)
    else:
        # method 2 not so smooth region
        cv2.fillPoly(mask, points, (255))

    res = cv2.bitwise_and(image, image, mask=mask)
    rect = cv2.boundingRect(points)  # returns (x,y,w,h) of the rect
    cropped = res[rect[1]: rect[1] + rect[3], rect[0]: rect[0] + rect[2]]

    # export corpped region
    cv2.imwrite(file_path, cropped)


def export_detected_regions(image_path, image, regions,
                            output_dir: str = "output/",
                            smooth_contour: bool = False):
    """
    Arguments:
        image_path: path to original image
        image: full/original image
        regions: list of bboxes or polys
        output_dir: folder to be exported
        smooth_contour: if true, curved/smoothed region will be cropped
    """
    # deepcopy image so that original is not altered
    image = copy.deepcopy(image)

    # get file name
    file_name, file_ext = os.path.splitext(os.path.basename(image_path))

    # create crops dir
    crops_dir = os.path.join(output_dir, file_name + "_crops")
    create_dir(crops_dir)

    for ind, region in enumerate(regions):
        file_path = os.path.join(crops_dir, "crop_" + str(ind) + ".png")
        export_detected_region(image,
                               points=region,
                               file_path=file_path,
                               smooth_contour=smooth_contour)


def export_extra_results(image_path,
                         image,
                         regions,
                         heatmap,
                         output_dir='output/',
                         verticals=None,
                         texts=None):
    """ save text detection result one by one
    Args:
        image_path (str): image file name
        image (array): raw image context
        boxes (array): array of result file
            Shape: [num_detections, 4] for BB output / [num_detections, 4]
            for QUAD output
    Return:
        None
    """
    image = np.array(image)

    # make result file list
    filename, file_ext = os.path.splitext(os.path.basename(image_path))

    # result directory
    res_file = os.path.join(output_dir,
                            "result_" + filename + '.txt')
    res_img_file = os.path.join(output_dir,
                                "result_" + filename + '.jpg')
    heatmap_file = os.path.join(output_dir,
                                "result_" + filename + '_heatmap.jpg')

    # create output dir
    create_dir(output_dir)

    # export heatmap
    cv2.imwrite(heatmap_file, heatmap)

    with open(res_file, 'w') as f:
        for i, region in enumerate(regions):
            region = np.array(region).astype(np.int32).reshape((-1))
            strResult = ','.join([str(r) for r in region]) + '\r\n'
            f.write(strResult)

            region = region.reshape(-1, 2)
            cv2.polylines(image,
                          [region.reshape((-1, 1, 2))],
                          True,
                          color=(0, 0, 255),
                          thickness=2)
#            ptColor = (0, 255, 255)
#            if verticals is not None:
#                if verticals[i]:
#                    ptColor = (255, 0, 0)

            if texts is not None:
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.5
                cv2.putText(image, "{}".format(texts[i]),
                            (region[0][0]+1, region[0][1]+1),
                            font,
                            font_scale,
                            (0, 0, 0),
                            thickness=1)
                cv2.putText(image,
                            "{}".format(texts[i]),
                            tuple(region[0]),
                            font,
                            font_scale,
                            (0, 255, 255),
                            thickness=1)

    # Save result image
    cv2.imwrite(res_img_file, image)
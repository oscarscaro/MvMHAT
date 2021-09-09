from torch.utils.data import Dataset
from collections import defaultdict
import os
import numpy as np
import cv2
import random
import re
import config as C

class Loader(Dataset):
    def __init__(self, views=2, frames=2, mode='train', dataset='1'):
        self.views = views
        self.mode = mode
        self.dataset = dataset
        self.down_sample = 1
        self.root_dir = '/dataset/gyy/mot/dataset'
        self.dataset_dir = os.path.join(self.root_dir, dataset)

        if self.mode == 'train':
            self.cut_dict = {
                '1': [0, 800],
                '2': [0, 800],
                '3': [0, 1000],
                '4': [0, 800],
                '5': [0, 1000],
                '6': [0, 1000],
                '7': [0, 2000],
                '8': [1000, 3000],
                '9': [2000, 4000],
                '10': [3000, 5000],
                '11': [500, 1500],
                '12': [500, 1500],
                '13': [1000, 3000],
            }
        else:
            self.cut_dict = {
                '1': [800, 1200],
                '2': [800, 1200],
                '3': [1000, 1500],
                '4': [800, 1200],
                '5': [1000, 1500],
                '6': [1000, 1500],
                '7': [2000, 2500],
                '8': [3000, 4000],
                '9': [4000, 5000],
                '10': [5000, 6000],
                '11': [1500, 2000],
                '12': [1500, 2000],
                '13': [3000, 4000],
            }
        if self.mode == 'train':
            self.frames = frames
            self.isShuffle = C.DATASET_SHUFFLE
            self.isCut = 1
        elif self.mode == 'test':
            self.frames = 1
            self.isShuffle = 0
            self.isCut = 1

        self.view_ls = os.listdir(self.dataset_dir)[:views]
        self.img_dict = self.gen_path_dict(False)
        self.anno_dict = self.gen_anno_dict()

    def gen_path_dict(self, drop_last: bool):
        path_dict = defaultdict(list)
        for view in self.view_ls:
            dir = os.path.join(self.dataset_dir, view, 'images')
            path_ls = os.listdir(dir)
            # path_ls.sort(key=lambda x: int(x[:-4]))
            path_ls.sort(key=lambda x: int(re.search(r"\d*", x).group()))
            path_ls = [os.path.join(dir, i) for i in path_ls]
            if self.isCut:
                start, end = self.cut_dict[self.dataset][0], self.cut_dict[self.dataset][1]
                path_ls = path_ls[start:end]
            if drop_last:
                path_ls = path_ls[:-1]
            cut = len(path_ls) % self.frames
            if cut:
                path_ls = path_ls[:-cut]
            if self.isShuffle:
                random.seed(self.isShuffle)
                random.shuffle(path_ls)
            path_dict[view] += path_ls
        path_dict = {view: [path_dict[view][i:i+self.frames] for i in range(0, len(path_dict[view]), self.frames)] for view in path_dict}
        return path_dict

    def gen_anno_dict(self):
        anno_dict = {}
        for view in self.view_ls:
            anno_view_dict = defaultdict(list)
            if self.mode == 'train':
                anno_path = os.path.join(self.dataset_dir, view, 'gt_det', 'gt.txt')
            elif self.mode == 'test':
                anno_path = os.path.join(self.dataset_dir, view, 'gt_det', 'det.txt')
            with open(anno_path, 'r') as anno_file:
                anno_lines = anno_file.readlines()
                for anno_line in anno_lines:
                    # if self.mode == 'train':
                    #     anno_line_ls = anno_line.split(',')
                    # else:
                    #     anno_line_ls = anno_line.split(' ')
                    anno_line_ls = anno_line.split(',')
                    anno_key = str(int(anno_line_ls[0]))
                    anno_view_dict[anno_key].append(anno_line_ls)
            anno_dict[view] = anno_view_dict
        return anno_dict

    def read_anno(self, path: str):
        path_split = path.split('/')
        view = path_split[-3]
        frame = str(int(re.search(r"\d*", path_split[-1]).group()))
        annos = self.anno_dict[view][frame]
        bbox_dict = {}
        for anno in annos:
            bbox = anno[2:6]
            bbox = [int(float(i)) for i in bbox]
            bbox_dict[anno[1]] = bbox
        return bbox_dict

    def crop_img(self, frame_img, bbox_dict):
        img = cv2.imread(frame_img)
        c_img_ls = []
        bbox_ls = []
        label_ls = []
        for key in bbox_dict:
            bbox = bbox_dict[key]
            bbox = [0 if i < 0 else i for i in bbox]
            # c_img_ls.append(img[bbox[0]:bbox[2], bbox[1]:bbox[3], :])
            crop = img[bbox[1]:bbox[3] + bbox[1], bbox[0]:bbox[2] + bbox[0], :]
            crop = cv2.resize(crop, (224, 224)).transpose(2, 0, 1).astype(np.float32)
            c_img_ls.append(crop)
            bbox_ls.append(bbox)
            label_ls.append(key)
        return np.stack(c_img_ls), bbox_ls, label_ls, frame_img

    def __len__(self):
        # return self.len
        return min([len(self.img_dict[i]) for i in self.view_ls] + [10000])

    def __getitem__(self, item):
        ret = []
        img_ls = [self.img_dict[view][item] for view in self.view_ls]

        for img_view in img_ls:
            view_ls = []
            for img in img_view:
                anno = self.read_anno(img)
                if anno == {}:
                    if self.mode == 'train':
                        return self.__getitem__(item - 1)
                    else:
                        view_ls.append([])
                        continue
                view_ls.append(self.crop_img(img, anno))
            ret.append(view_ls)
        return ret



if __name__ == '__main__':
    a = Loader(mode='train', dataset='1')
    for i in enumerate(a):
        pass







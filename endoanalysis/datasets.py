import os
import cv2
import yaml
from tqdm import tqdm
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import patches, cm
import albumentations as A
from endoanalysis.targets import Keypoints, keypoints_list_to_batch, load_keypoints
from endoanalysis.nucprop import visualize_masks




def extract_images_and_labels_paths(images_list_file, labels_list_file):
    
    images_list_dir = os.path.dirname(images_list_file)
    labels_list_dir = os.path.dirname(labels_list_file)

    with open(images_list_file, "r") as images_file:
        images = images_file.readlines()
        images = [os.path.normpath(os.path.join(images_list_dir,x.strip())) for x in images]
    with open(labels_list_file, "r") as labels_file:
        labels = labels_file.readlines()
        labels = [os.path.normpath(os.path.join(labels_list_dir,x.strip())) for x in labels]
    
    check_images_and_labels_pathes(images, labels)
    
    return images, labels



def agregate_images_and_labels_paths(images_lists, labels_lists):
    
    if type(images_lists) != type(labels_lists):
            raise Exception("images_list_files and labels_list_file should have the same type")
            
    if type(images_lists) != list:
        images_lists = [images_lists]
        labels_lists = [labels_lists]
            
    images_paths = []
    labels_paths = []
    for images_list_path, labels_list_path in zip(images_lists, labels_lists):
        images_paths_current, labels_paths_current = extract_images_and_labels_paths(images_list_path, labels_list_path)
        images_paths += images_paths_current
        labels_paths += labels_paths_current
        
    return images_paths, labels_paths


def check_images_and_labels_pathes(images_paths, labels_paths):
    

    if len(images_paths) != len(labels_paths):
        raise Exception("Numbers of images and labels are not equal")
        
    for image_path, labels_path in zip(images_paths, labels_paths):
        dirname_image = os.path.dirname(image_path)
        dirname_labels = os.path.dirname(labels_path)
        filename_image = os.path.basename(image_path)
        filename_labels = os.path.basename(labels_path)
     
        if ".".join(filename_image.split(".")[:-1]) != ".".join(filename_labels.split(".")[:-1]):
            raise Exception("Different dirnames found: \n %s\n  %s"%(images_paths, labels_paths))


def load_image(image_path):
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return image


class PointsDataset:
    
    def __init__(
        self,
        images_list,
        labels_list,
        keypoints_dtype=np.float,
        cmap_kwargs = {"cmap": cm.Set1, "period": 8}
    ):

            
        self.keypoints_dtype = keypoints_dtype
 
        self.images_paths, self.labels_paths = agregate_images_and_labels_paths(images_list, labels_list,)
        self.cmap_kwargs = cmap_kwargs
        
    def __len__(self):
        return len(self.images_paths)

    def __getitem__(self, x):
        
       
        image = load_image(self.images_paths[x])
        keypoints = load_keypoints(self.labels_paths[x])

        class_labels = [x[-1] for x in keypoints]
        keypoints_no_class = [x[:-1] for x in keypoints]

        keypoints = [
            np.array(y + (x,)) for x, y in zip(class_labels, keypoints_no_class)
        ]
        
        if keypoints:
            keypoints = np.stack(keypoints)
        else:
            keypoints = np.empty((0,3))

        to_return = {
            "keypoints": Keypoints(keypoints.astype(self.keypoints_dtype))
        }


        to_return["image"] = image

        return to_return


    def visualize(
        self,
        x,
        show_labels=True,
        image_key="image",
        print_labels=False,
        labels_kwargs={"radius": 3, "alpha": 1.0},
        cmap_kwargs = None 
    ):
        
        if cmap_kwargs is None:
            cmap_kwargs = self.cmap_kwargs
            
        sample = self[x]
        image = sample[image_key]
        keypoints = sample["keypoints"]
        fig, ax = plt.subplots()

        ax.imshow(image)
        x_coords = keypoints.x_coords()
        y_coords = keypoints.y_coords()
        classes = keypoints.classes()

        if show_labels:
            for center_x, center_y, obj_class in zip(x_coords, y_coords, classes):
                
                if "period" not in cmap_kwargs:
                    color = cmap_kwargs["cmap"](obj_class)
                else:
                    color = cmap_kwargs["cmap"](obj_class % cmap_kwargs["period"])
                
                patch = patches.Circle((center_x, center_y), color=color, **labels_kwargs)

                ax.add_patch(patch)
        if print_labels:
            for keypoint_i, keypoint in enumerate(keypoints_tuples):
                print("%i. %i, %f, %f, %f, %f" % ((keypoint_i,) + keypoint))
                
                
    def collate(self):

        images = [self[x]["image"] for x in range(len(self))]
        keypoints_groups = [self[x]["keypoints"] for x in range(len(self))]

        return_dict = {
            "image": np.stack(images, 0),
            "keypoints": keypoints_list_to_batch(keypoints_groups),
        }

        return return_dict

          
class MasksDataset:
    
    def __init__(
        self,
        images_list,
        masks_list,
        cmap_kwargs = {"cmap": cm.Set1, "period": 8}
    ):

            
        
        if type(images_list) != type(masks_list):
            raise Exception("images_list and masks_list should have the same type")
            
        if type(images_list) != list:
            images_list = [images_list]
            masks_list = [masks_list]
            
        self.images_paths = []
        self.masks_paths = []
        for images_list_path, masks_list_path in zip(images_list, masks_list):
            images_paths_current, masks_paths_current = extract_images_and_labels_paths(images_list_path, masks_list_path)
            self.images_paths += images_paths_current
            self.masks_paths += masks_paths_current
        self.cmap_kwargs = cmap_kwargs
        
    def __len__(self):
        return len(self.images_paths)

    def __getitem__(self, x):
        
        masks_array = np.load(self.masks_paths[x])

        return {
            "image": load_image(self.images_paths[x]),
            "masks": masks_array["masks"],
            "classes": masks_array["classes"]
            
        }


    def visualize(
        self,
        x,
        show_labels=True,
        image_key="image",

        cmap_kwargs = None 
    ):
        
        if cmap_kwargs is None:
            cmap_kwargs = self.cmap_kwargs
            
        sample = self[x]
        image = sample[image_key]
        visualize_masks(sample["image"], sample["masks"])

                
def resize_dataset(image_paths, labels_paths, target_size=(256,256)):
    
    transorm = A.Compose([A.Resize(height=target_size[0], width=target_size[1])], keypoint_params=A.KeypointParams(format="xy"))

    
    with tqdm(total=len(image_paths)) as pbar:
        for image_path, labels_path in zip(image_paths, labels_paths):

            image = image = cv2.imread(image_path)

            keypoints = load_keypoints(labels_path)

            if keypoints:
                keypoints = np.array(keypoints)
                coords = keypoints[:,0:2]
                classes = keypoints[:,2]
            else: 
                coords = []
            transformed = transorm(image = image, keypoints=coords)

            cv2.imwrite(image_path, transformed["image"])

            labels_lines = [
                " ".join([str(int(y)) for y in label] + [str(class_id)]) + " \n"
                for label, class_id in zip(transformed["keypoints"], classes)
                ]

            os.remove(labels_path)

            with open(labels_path, "w+") as labels_file:
                labels_file.writelines(labels_lines)
            pbar.update()
            
def parse_master_yaml(yaml_path):
    """
    Imports master yaml and converts paths to make the usable from inside the script
    
    Parameters
    ----------
    yaml_path : str
        path to master yaml from the script
    
    Returns
    -------
    lists : dict of list of str
        dict with lists pf converted paths
    """
    with open(yaml_path, "r") as file:
        lists = yaml.safe_load(file)
        
    
    for list_type, paths_list in lists.items():
        new_paths_list = []
        for path in paths_list:
            new_path = os.path.join(os.path.dirname(yaml_path), path)
            new_path = os.path.normpath(new_path)
            new_paths_list.append(new_path)
        lists[list_type] = new_paths_list


    return lists
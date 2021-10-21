# Description

This is a supplementary repository for EndoNuke dataset. The dataset can be
 accessed at [endnuke.ispras.ru](endnuke.ispras.ru). The code here is the
 implementation of the methods described in the corresponding paper and also
 provides some useful tools to use this dataset. It's up to a user to decide,
 whether to use them or to create the original methods.


 # Installation

 To install the package make sure, that the  `python3`  and `pip`. We recommend
 to use `python3.8` and `pip v21.1.1`. To run a dip test on
staining distributions, it's also necessary to have `R` installed.

For all subsequent actions we strongly recommend to use `venv` module to keep
the system `python` unspoiled.

After all aforementioned packages are set up, run the following lines to
install the package `endoanalysis`:

```
git clone ...
cd endometrium-dataset-analysis
pip install .
```
To test an installation run:

```
pip list | grep endometrium
```
The result must contain the line starting with `endometrium-dataset-analysis`

# Methods from the paper
Before folloing the instructions presented here it's hihgly teccomended to read the paper.
To reproduce the analysis presented in the paper the following steps should be
 followed:
<ol>
  <li>

   Download the dataset from [endnuke.ispras.ru](endnuke.ispras.ru) and
    extract the archive. We assume, that the dataset is extracted in the directory
    `endometrium-dataset-analysis/data/dataset` and master yml files are extracted
    to `endometrium-dataset-analysis/data/master_ymls` Then go to the directory with the scripts, ehicvwhich is `endometrium-dataset-analysis/scripts`.

  </li>
  <p></p>
  <li>
  Run the script to resize the dataset images and annotations
  (note, that the resize is done in-place):

  ```
  python resize_dataset.py --master ../data/master_ymls/everything.yaml --size 256,256
  ```
  </li>
  <p></p>
  <li>
  Run the script to generate the masks without any size filtering:

  ```
  python generate_masks.py --master ../data/master_ymls/unique.yaml --workers 8 --window 100 --avg_area 20 --area_flags --new_master_dir ../data/masks/masks_raw --compress
  ```
   These masks will be saved to `endometrium-dataset-analysis/data/masks/masks_raw` dir.
  </li>
  <p></p>
  <li>

  Go through obtain the mean radius and area thresholds using the following `mean_raduis.ipynb` notebook:

  ```
  jupyter-notebook ../notebooks/mean_raduis.ipynb
  ```
  or just use the values **23** for small outliers threshold, **658** for large threshold and **163** as average area.
  </li>
  <p></p>
  <li>
  Run the script to generate filtered full masks (masks of fixed size):

  ```
  python generate_masks.py --master ../data/master_ymls/unique.yaml --workers 8 --window 100 --avg_area 163 --min_area 23 --max_area 658 --area_flags --new_master_dir ../data/masks/masks_full --compress
  ```

  These masks will be saved to `endometrium-dataset-analysis/data/masks/masks_full` dir.
  </li>
  <p></p>
  <li>
  Run the script to generate "probes" masks (masks of fixed size):

  ```
  python generate_masks.py --master ../data/master_ymls/unique.yaml --workers 8 --window 100 --avg_area 20 --min_area 1000000000 --area_flags --new_master_dir ../data/masks/masks_probes --compress
  ```

  These masks will be saved to `endometrium-dataset-analysis/data/masks/masks_probes` dir.
  </li>
  <p></p>
  <li>
  Run the scripts to calculate dab values for probe and full mask methods:

  ```
  python dab_values.py --master ../data/masks/masks_full/unique_with_masks.yml --bin_out ../data/dab_values/full.npy
  python dab_values.py --master ../data/masks/masks_probes/unique_with_masks.yml --bin_out ../data/dab_values/probes.npy
  ```
  </li>
  <p></p>
  <li>

  Finally, go through `staining.ipynb` notebook to perform the dip tests and Kolmogorov-Smirnov test (note, that for this step `R` should be installed so `rpy2` package is operational):

  ```
  jupyter-notebook ../notebooks/staining.ipynb
  ```
  </li>
</ol>
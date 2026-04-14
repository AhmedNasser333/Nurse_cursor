"""
Local override: upstream p4a still ships opencv_extras at 4.5.1 while opencv is 4.12.0,
which breaks the build. This recipe must match pythonforandroid.recipes.opencv version.
"""
from pythonforandroid.recipe import Recipe


class OpenCVExtrasRecipe(Recipe):
    version = "4.12.0"
    url = "https://github.com/opencv/opencv_contrib/archive/{version}.zip"
    depends = ["opencv"]


recipe = OpenCVExtrasRecipe()

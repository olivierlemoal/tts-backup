import json
import re
import os


IMGPATH = os.path.join("Mods", "Images")
OBJPATH = os.path.join("Mods", "Models")
BUNDLEPATH = os.path.join("Mods", "Assetbundles")

if os.name == 'nt':
    GAMEDATA_DEFAULT = os.path.expanduser(
        "~/Documents/My Games/Tabletop Simulator"
    )
elif os.name == 'posix':
    GAMEDATA_DEFAULT = os.path.expanduser(
        "~/.local/share/Tabletop Simulator"
    )


class NoImageExtensionException(Exception):

    def __init__(self, filename_no_ext):
        super().__init__(self)
        self.filename_no_ext = filename_no_ext


def seekURL(dic, trail=[]):
    """Recursively search through the save game structure and return URLs
    and the paths to them.

    """

    for k, v in dic.items():

        newtrail = trail + [k]

        if isinstance(v, dict):
            yield from seekURL(v, newtrail)

        elif isinstance(v, list):
            for elem in v:
                if not isinstance(elem, dict):
                    continue
                yield from seekURL(elem, newtrail)

        elif k.endswith("URL"):
            # We don’t want tablet URLs.
            if k == "PageURL":
                continue

            # Some URL keys may be left empty.
            if not v:
                continue

            # Deck art URLs can contain metadata in curly braces
            # (yikes).
            v = re.sub(r"{.*}", "", v)

            yield (newtrail, v)


# We need checks for whether a URL points to a mesh or an image, so we
# can do the right thing for each.

def is_obj(path, url):
    # TODO: None of my mods have NormalURL set (normal maps?). I’m
    # assuming these are image files.
    obj_keys = ("MeshURL", "ColliderURL")
    return path[-1] in obj_keys


def is_image(path, url):
    # This assumes that we only have mesh, assetbundle and image URLs.
    return not (is_obj(path, url) or is_assetbundle(path, url))


def is_assetbundle(path, url):
    bundle_keys = ("AssetbundleURL", "AssetbundleSecondaryURL")
    return path[-1] in bundle_keys


def recodeURL(url):
    """Recode the given URL in the way TTS does, which yields the
    file-system path to the cached file."""

    return re.sub(r"[\W_]", "", url)


def get_fs_path(path, url):
    """Return a file-system path to the object in the cache."""

    recoded_name = recodeURL(url)

    if is_obj(path, url):
        filename = recoded_name + ".obj"
        return os.path.join(OBJPATH, filename)

    elif is_assetbundle(path, url):
        filename = recoded_name + ".unity3d"
        return os.path.join(BUNDLEPATH, filename)

    elif is_image(path, url):
        # Find local image
        filename = find_image(url)
        if filename:
            return filename

        if ".png" in url:
            file_suffix = ".png"
        elif ".jpeg" in url or ".jpg" in url:
            file_suffix = ".jpg"
        else:
            filename_no_ext = os.path.join(IMGPATH, recoded_name)
            raise NoImageExtensionException(filename_no_ext)

        filename = recoded_name + file_suffix
        return os.path.join(IMGPATH, filename)

    else:
        errstr = ("Do not know how to generate path for "
                  "URL {url} at {path}.".format(url=url, path=path))
        raise ValueError(errstr)


def find_image(url):
    # Determin if file exists
    recoded_name = recodeURL(url)

    image_path_no_ext = os.path.join(GAMEDATA_DEFAULT, IMGPATH, recoded_name)
    if os.path.exists(image_path_no_ext + ".jpg"):
        return os.path.join(IMGPATH, recoded_name + ".jpg")
    elif os.path.exists(image_path_no_ext + ".png"):
        return os.path.join(IMGPATH, recoded_name + ".png")
    return None

def urls_from_save(filename):

    with open(filename, 'r', encoding='utf-8') as infile:
        save = json.load(infile)
    return seekURL(save)


def get_save_name(filename):

    with open(filename, 'r', encoding='utf-8') as infile:
        save = json.load(infile)
    return save["SaveName"]

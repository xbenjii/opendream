import json
from . import reference
from .layer import Layer
from .canvas import Canvas

CANVAS = Canvas()
DEBUG = True

operators = {}

# decorator to make a function into a dream operator
def define_op(func):

    def wrapper(*args, **kwargs):

        # Run decorated function
        layer = func(*args, **kwargs)

        # iterate through args / kwargs, replace layer objects with layer names (makes metadata compact)
        lm_args = list(args)   
        lm_kwargs = kwargs.copy()
        for i in range(len(lm_args)):
            lm_args[i] = lm_args[i].get_id() if isinstance(lm_args[i], Layer) else lm_args[i]
        for key, value in lm_kwargs.items():
            lm_kwargs[key] = value.get_id() if isinstance(value, Layer) else value
        
        # create layer, provide operation and arguments as metadata
        layer.set_metadata({"op": func.__name__, "params": lm_args, "options": lm_kwargs})

        # add to CANVAS
        CANVAS.add_layer(layer)
        return layer
        
    operators[func.__name__] = func 
    return wrapper


def save(json_file_path: str = "opendream.json"):

    ordering = CANVAS.get_ordering()
    data = {}

    # Iterate through layer list, write metadata to dictionary
    for i, layer_name in enumerate(ordering):
        layer = CANVAS.get_layer(layer_name)
        data[layer_name] = layer.get_metadata()

    # Write dictionary to disk
    with open(json_file_path, 'w') as outfile:
        json.dump(data, outfile, indent = 4)

@define_op
def dream(prompt: str, model_ckpt: str = "runwayml/stable-diffusion-v1-5", seed: int = 42, device: str = "mps", batch_size: int = 1, selected: int = 0, num_steps: int = 20, guidance_scale: float = 7.5, **kwargs):
    return reference.dream(prompt, model_ckpt, seed, device, batch_size, selected, num_steps, guidance_scale, **kwargs)

@define_op
def mask_and_inpaint(mask_image: Layer, image: Layer, prompt: str, model_ckpt: str = "runwayml/stable-diffusion-inpainting", seed: int = 42, device: str = "mps", batch_size: int = 1, selected: int = 0, num_steps: int = 20, guidance_scale: float = 7.5, **kwargs):
    return reference.mask_and_inpaint(mask_image, image, prompt, model_ckpt, seed, device, batch_size, selected, num_steps, guidance_scale, **kwargs)

@define_op
def make_dummy_mask():
    return reference.make_dummy_mask()

@define_op
def load_image_from_path(path: str):
    return Layer.from_path(path)

def execute(json_file_path: str):
    
    # delete all files in debug folder
    if DEBUG:
        import os
        for filename in os.listdir("debug/"):
            os.remove(f"debug/{filename}")

    # Execute operations outlined in json
    with open(json_file_path) as json_file:
        data = json.load(json_file)
        for _, layer_metadata in data.items():
            try:
                # retrieve function corresponding to json operation
                func = operators[layer_metadata["op"]]
                
                # cross-reference layer names with layers in canvas
                for index, arg in enumerate(layer_metadata["params"]):
                    associated_layer = CANVAS.get_layer(arg)
                    if associated_layer is not None:
                        layer_metadata["params"][index] = associated_layer
                
                # run function with arguments
                layer = define_op(func)(*layer_metadata["params"], **layer_metadata["options"])
                
            except Exception as e:
                print(f"Error executing {layer_metadata['op']}: {e}")
                raise e

    return CANVAS
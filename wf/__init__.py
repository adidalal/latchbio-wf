"""
LatchBio implementation of the Allen Cell & Structure Segmenter toolkit
"""

import importlib
from enum import Enum
from pathlib import Path

from aicsimageio import imread
from latch import small_task, workflow
from latch.types import LatchAuthor, LatchFile, LatchMetadata, LatchParameter

IMAGE_SCALING: dict[str, int] = {'cetn2': 5100}
BASE_IMAGE_DIMENSIONS: tuple[int, int, int] = (128, 128, 128)
RESCALE_RATIO: float = 0.7
DEFAULT_IMAGE = '/root/reference/random_input.tiff'
IMAGE_OUTPUT_FOLDER: str = '/root/wf/'

"""
Segmentation types are from allencell.org/segmenter.html#lookup-table
Segmentation values are from github.com/AllenCell/aics-segmentation/tree/main/aicssegmentation/structure_wrapper
"""


# noinspection SpellCheckingInspection
class SegmentationType(Enum):
    actb = 'Alpha tubulin'
    actn1 = 'Alpha-actinin-1'
    cetn2 = 'Centrin-2'
    fbl = 'Fibrillarin'
    h2b_interphase = 'H2B (interphase-specific)'
    lamp1 = 'LAMP-1'
    lmnb1_interphase = 'Lamin B1 (interphase-specific)'
    lmnb1_mitotic = 'Lamin B1 (mitosis-specific)'
    npm1 = 'Nucleophosmin'
    nup153 = 'Nup153'
    pxn = 'Paxillin'
    rab5a = 'Rab-5A'
    sec61b = 'Sec61 beta'
    smc1a = 'SMC1A'
    son = 'SON'
    tomm20 = 'TOM20'


def run_segmentation(input_file: Path, structure_name: SegmentationType, output_type: str = 'default'):
    input_file_path = input_file.resolve(strict=True)

    # dynamically load segmentation module
    structure_name = structure_name.name.lower()
    try:
        module_name = f'aicssegmentation.structure_wrapper.seg_{structure_name}'
        seg_module = importlib.import_module(module_name)
        function_name = f'Workflow_{structure_name}'
        seg_module_function = getattr(seg_module, function_name)
    except Exception as e:
        print(f'raising failure while trying to activate module for {structure_name}')
        raise e

    # load image
    input_array = imread(input_file_path).reshape(*BASE_IMAGE_DIMENSIONS)
    input_array *= IMAGE_SCALING.get(structure_name, 1)

    # conduct segmentation
    output_array = seg_module_function(
        struct_img=input_array,
        rescale_ratio=RESCALE_RATIO,
        output_type=output_type,
        output_path=IMAGE_OUTPUT_FOLDER,
        fn=f'processed_{structure_name}',
    )

    return output_array


@small_task
def seg_task(
        segmentation_type: SegmentationType,
        input_file: LatchFile = LatchFile(DEFAULT_IMAGE),
) -> LatchFile:
    input_file_path: Path = Path(input_file)
    seg_type: str = segmentation_type.name.lower()
    output_data = run_segmentation(input_file_path, segmentation_type)
    return LatchFile(f'{IMAGE_OUTPUT_FOLDER}/processed_{seg_type}_struct_segmentation.tiff',
                     f'latch:///processed_{seg_type}_struct_segmentation.tiff')


metadata = LatchMetadata(
    display_name="Allen Cell and Structure Segmenter toolkit",
    documentation="https://www.allencell.org/segmenter.html",
    author=LatchAuthor(
        name="Aditya Dalal",
        email="null@example.com",
        github="https://github.com/adidalal",
    ),
    repository="https://github.com/adidalal/latchbio-wf",
    license="",
    parameters={
        "input_file": LatchParameter(
            display_name="Input Data file",
            description="Select a file or input URL/URI...",
            batch_table_column=True,
        ),
        "segmentation_type": LatchParameter(
            display_name="Segmentation type",
            description="Select segmentation type - see allencell.org/segmenter.html#lookup-table",
            batch_table_column=True,
        ),
    },
)


@workflow(metadata)
def run_image_processing(input_file: LatchFile, segmentation_type: SegmentationType) -> LatchFile:
    """
    This is a LatchBio workflow that is an implementation of the [Allen Cell & Structure Segmenter](https://www.allencell.org/segmenter.html) toolkit. The purpose of this library is to provide 3D segmentation of intracellular structures in fluorescence microscopy images.

    While it is possible to provide the pre-processing, core segmentation algorithm and post-processing primitives directly to the user, it is not conducive to a smooth user workflow due to the large amount of experimental trial and error required.

    Based on the current state of the art, a variety of [classic image segmentation workflows](https://www.allencell.org/segmenter.html#lookup-table) have been provided, for the user to select the one most similar to the input data's characteristics as a starting point.

    **Note:** The underlying library supports both a classic image segmentation and an iterative deep learning workflow. In the current implementation, only the classic segmentation is supported.

    ## Usage

    See the "Parameters" tab. Briefly, there are a few components:

    - Image upload - accepts any well-formatted TIFF file
    - Selection of segmentation workflow - please see [this page](https://www.allencell.org/segmenter.html#lookup-table) for larger images and supplementary videos
    - Additional options to tweak the segmentation parameters

    The output will be your segmented image.

    [More information](https://github.com/adidalal/latchbio-wf)
    """
    processed_output = seg_task(input_file=input_file, segmentation_type=segmentation_type)
    return processed_output

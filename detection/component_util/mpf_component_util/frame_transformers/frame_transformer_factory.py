#############################################################################
# NOTICE                                                                    #
#                                                                           #
# This software (or technical data) was produced for the U.S. Government    #
# under contract, and is subject to the Rights in Data-General Clause       #
# 52.227-14, Alt. IV (DEC 2007).                                            #
#                                                                           #
# Copyright 2018 The MITRE Corporation. All Rights Reserved.                #
#############################################################################

#############################################################################
# Copyright 2018 The MITRE Corporation                                      #
#                                                                           #
# Licensed under the Apache License, Version 2.0 (the "License");           #
# you may not use this file except in compliance with the License.          #
# You may obtain a copy of the License at                                   #
#                                                                           #
#    http://www.apache.org/licenses/LICENSE-2.0                             #
#                                                                           #
# Unless required by applicable law or agreed to in writing, software       #
# distributed under the License is distributed on an "AS IS" BASIS,         #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  #
# See the License for the specific language governing permissions and       #
# limitations under the License.                                            #
#############################################################################


from . import frame_transformer, frame_rotator, frame_flipper, frame_cropper
from .. import utils


def get_transformer(job, input_frame_size):
    ff_frame_locations = dict()
    if hasattr(job, 'feed_forward_track'):
        if job.feed_forward_track is not None:
            ff_frame_locations = job.feed_forward_track.frame_locations

    elif hasattr(job, 'feed_forward_location'):
        if job.feed_forward_location is not None:
            ff_frame_locations = {0: job.feed_forward_location}

    return _get_transformer(job, input_frame_size, ff_frame_locations)



def _get_transformer(job, input_frame_size, ff_frame_locations):
    transformer = frame_transformer.NoOpTransformer(input_frame_size)

    transformer = _add_rotator_if_needed(job.job_properties, job.media_properties, transformer)
    transformer = _add_flipper_if_needed(job.job_properties, job.media_properties, transformer)
    transformer = _add_cropper_if_needed(job, input_frame_size, ff_frame_locations, transformer)

    return transformer



def _add_rotator_if_needed(job_properties, media_properties, current_transformer):
    if utils.get_property(job_properties, 'AUTO_ROTATE', False):
        rotation = utils.get_property(media_properties, 'ROTATION', 0)
    else:
        rotation = utils.get_property(job_properties, 'ROTATION', 0)

    if rotation not in (0, 90, 180, 270):
        raise ValueError('Rotation degrees must be 0, 90, 180, or 270.')

    if rotation == 0:
        return current_transformer
    else:
        return frame_rotator.FrameRotator(current_transformer, rotation)



def _add_flipper_if_needed(job_properties, media_properties, current_transformer):
    if utils.get_property(job_properties, 'AUTO_FLIP', False):
        should_flip = utils.get_property(media_properties, 'HORIZONTAL_FLIP', False)
    else:
        should_flip = utils.get_property(job_properties, 'HORIZONTAL_FLIP', False)

    if should_flip:
        return frame_flipper.FrameFlipper(current_transformer)
    else:
        return current_transformer


def _add_cropper_if_needed(job, input_frame_size, ff_frame_locations, current_transformer):
    exact_region_enabled = 'REGION' == job.job_properties.get('FEED_FORWARD_TYPE', '').upper()
    superset_region_enabled = 'SUPERSET_REGION' == job.job_properties.get('FEED_FORWARD_TYPE', '').upper()
    search_region_enabled = utils.get_property(job.job_properties, 'SEARCH_REGION_ENABLE_DETECTION', False)

    if not exact_region_enabled and not superset_region_enabled and not search_region_enabled:
        return current_transformer

    if exact_region_enabled:
        return frame_cropper.FeedForwardFrameCropper(current_transformer, ff_frame_locations)

    if superset_region_enabled:
        region_of_interest = _get_superset_region(ff_frame_locations)
    else:
        region_of_interest = _get_search_region(job.job_properties, input_frame_size)

    region_is_entire_frame = region_of_interest == utils.Rect(0, 0, *input_frame_size)

    if region_is_entire_frame:
        return current_transformer
    else:
        return frame_cropper.SearchRegionFrameCropper(current_transformer, region_of_interest)



def _get_superset_region(ff_frame_locations):
    if not ff_frame_locations:
        raise IndexError('FEED_FORWARD_TYPE: SUPERSET_REGION is enabled, but feed forward track was empty.')

    image_location_iter = ff_frame_locations.itervalues()
    first_loc = image_location_iter.next()

    region = utils.Rect.from_image_location(first_loc)

    for image_loc in image_location_iter:
        region = region.union(utils.Rect.from_image_location(image_loc))
    return region



def _get_search_region(job_properties, input_frame_size):
    region_x = max(0, utils.get_property(job_properties, 'SEARCH_REGION_TOP_LEFT_X_DETECTION', 0))
    region_y = max(0, utils.get_property(job_properties, 'SEARCH_REGION_TOP_LEFT_Y_DETECTION', 0))

    region_br_x = utils.get_property(job_properties, 'SEARCH_REGION_BOTTOM_RIGHT_X_DETECTION', -1)
    if region_br_x <= 0:
        region_br_x = input_frame_size[0]

    region_br_y = utils.get_property(job_properties, 'SEARCH_REGION_BOTTOM_RIGHT_Y_DETECTION', -1)
    if region_br_y <= 0:
        region_br_y = input_frame_size[1]


    return utils.Rect.from_corners(utils.Point(region_x, region_y), utils.Point(region_br_x, region_br_y))

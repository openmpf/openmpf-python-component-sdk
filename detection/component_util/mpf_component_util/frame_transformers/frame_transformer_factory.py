#############################################################################
# NOTICE                                                                    #
#                                                                           #
# This software (or technical data) was produced for the U.S. Government    #
# under contract, and is subject to the Rights in Data-General Clause       #
# 52.227-14, Alt. IV (DEC 2007).                                            #
#                                                                           #
# Copyright 2023 The MITRE Corporation. All Rights Reserved.                #
#############################################################################

#############################################################################
# Copyright 2023 The MITRE Corporation                                      #
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

from __future__ import division, print_function

import sys
from typing import Dict, Iterable, Mapping, Tuple, Union

import mpf_component_api as mpf

from .affine_frame_transformer import AffineFrameTransformer, FeedForwardExactRegionAffineTransformer
from .frame_transformer import NoOpTransformer
from .frame_cropper import FeedForwardFrameCropper, SearchRegionFrameCropper
from .search_region import SearchRegion, RegionEdge
from .. import utils


def get_transformer(job: Union[mpf.VideoJob, mpf.ImageJob], input_frame_size):
    ff_frame_locations = dict()
    track_properties = dict()
    if hasattr(job, 'feed_forward_track'):
        if job.feed_forward_track is not None:
            ff_frame_locations = job.feed_forward_track.frame_locations
            track_properties = job.feed_forward_track.detection_properties

    elif hasattr(job, 'feed_forward_location'):
        if job.feed_forward_location is not None:
            ff_frame_locations = {0: job.feed_forward_location}

    return _get_transformer(job, input_frame_size, ff_frame_locations, track_properties)



def _get_transformer(job, input_frame_size, ff_frame_locations: Dict[int, mpf.ImageLocation], track_properties):
    transformer = NoOpTransformer(input_frame_size)

    if _feed_forward_is_enabled(job.job_properties):
        if not ff_frame_locations:
            raise ValueError('Feed forward is enabled, but feed forward track was empty.')
        return _add_feed_forward_transforms_if_needed(job.job_properties, job.media_properties, track_properties,
                                                      ff_frame_locations, transformer)
    else:
        return _add_transformers_if_needed(job.job_properties, job.media_properties, input_frame_size, transformer)



def _add_transformers_if_needed(job_properties, media_properties, input_video_size, current_transformer):
    _, rotation = _get_job_level_rotation(job_properties, media_properties)
    rotation = utils.normalize_angle(rotation)

    rotation_threshold = utils.get_property(job_properties, 'ROTATION_THRESHOLD', 0.1)
    rotation_required = not utils.rotation_angles_equal(rotation, 0, rotation_threshold)
    if not rotation_required:
        rotation = 0

    _, flip_required = _get_job_level_flip(job_properties, media_properties)

    search_region = _get_search_region(job_properties)
    if rotation_required or flip_required:
        return AffineFrameTransformer.search_region_on_rotated_frame(
            rotation, flip_required, _get_fill_color(job_properties), search_region,
            current_transformer)

    frame_rect = utils.Rect.from_corner_and_size((0, 0), input_video_size)
    search_region_rect = search_region.get_rect(input_video_size)
    if frame_rect == search_region_rect:
        return current_transformer
    return SearchRegionFrameCropper(search_region_rect, current_transformer)



def _add_feed_forward_transforms_if_needed(job_properties, media_properties, track_properties,
                                           detections: Dict[int, mpf.ImageLocation],
                                           current_transformer):
    if _search_region_cropping_is_enabled(job_properties):
        print('Both feed forward cropping and search region cropping properties were provided. '
              'Only feed forward cropping will occur.',
              file=sys.stderr)

    has_job_level_rotation, job_level_rotation = _get_job_level_rotation(job_properties, media_properties)
    has_job_level_flip, job_level_flip = _get_job_level_flip(job_properties, media_properties)

    has_track_level_rotation = 'ROTATION' in track_properties
    track_rotation = utils.normalize_angle(utils.get_property(track_properties, 'ROTATION', 0.0))

    has_track_level_flip = 'HORIZONTAL_FLIP' in track_properties
    track_level_flip = utils.get_property(track_properties, 'HORIZONTAL_FLIP', False)

    rotation_threshold = utils.get_property(job_properties, 'ROTATION_THRESHOLD', 0.1)
    any_detection_requires_rotation_or_flip = False
    is_exact_region_mode = _feed_forward_exact_region_is_enabled(job_properties)
    regions = []

    for detection in detections.values():
        has_detection_level_rotation = 'ROTATION' in detection.detection_properties
        rotation = 0.0
        if has_detection_level_rotation:
            rotation = utils.normalize_angle(float(detection.detection_properties['ROTATION']))
        elif has_track_level_rotation:
            rotation = track_rotation
        elif has_job_level_rotation and is_exact_region_mode:
            rotation = job_level_rotation
        current_detection_requires_rotation = not utils.rotation_angles_equal(rotation, 0,
                                                                              rotation_threshold)
        if not current_detection_requires_rotation:
            rotation = 0

        has_detection_level_flip = 'HORIZONTAL_FLIP' in detection.detection_properties
        current_detection_requires_flip = False
        if has_detection_level_flip:
            current_detection_requires_flip = utils.get_property(
                detection.detection_properties, 'HORIZONTAL_FLIP', False)
        elif has_track_level_flip:
            current_detection_requires_flip = track_level_flip
        elif has_job_level_flip and is_exact_region_mode:
            current_detection_requires_flip = job_level_flip

        if current_detection_requires_flip or current_detection_requires_rotation:
            any_detection_requires_rotation_or_flip = True

        regions.append(utils.RotatedRect(
            detection.x_left_upper, detection.y_left_upper, detection.width, detection.height,
            rotation, current_detection_requires_flip))

    if is_exact_region_mode:
        if any_detection_requires_rotation_or_flip:
            return FeedForwardExactRegionAffineTransformer(regions, _get_fill_color(job_properties),
                                                           current_transformer)
        else:
            return FeedForwardFrameCropper(detections, current_transformer)
    else:
        if any_detection_requires_rotation_or_flip:
            return AffineFrameTransformer.rotated_superset_region(
                regions, job_level_rotation, job_level_flip, _get_fill_color(job_properties),
                current_transformer)
        else:
            superset_region = _get_superset_region_no_rotation(regions)
            return SearchRegionFrameCropper(superset_region, current_transformer)




def _get_job_level_rotation(job_properties, media_properties):
    rotation_str = job_properties.get('ROTATION')
    if not rotation_str and utils.get_property(job_properties, 'AUTO_ROTATE', True):
        rotation_str = media_properties.get('ROTATION')
    if rotation_str:
        return True, utils.normalize_angle(float(rotation_str))
    else:
        return False, 0

def _get_job_level_flip(job_properties, media_properties):
    job_flip = utils.get_property(job_properties, 'HORIZONTAL_FLIP', None, bool)
    if job_flip is not None:
        return True, job_flip
    if utils.get_property(job_properties, 'AUTO_FLIP', True):
        media_flip = utils.get_property(media_properties, 'HORIZONTAL_FLIP', None, bool)
        if media_flip is not None:
            return True, media_flip
    return False, False


def _get_superset_region_no_rotation(regions: Iterable[utils.RotatedRect]) -> utils.Rect:
    if not regions:
        raise ValueError('FEED_FORWARD_TYPE: SUPERSET_REGION is enabled, but feed forward track was empty.')

    region_iter = iter(regions)

    region = next(region_iter).bounding_rect
    for next_region in region_iter:
        region = region.union(next_region.bounding_rect)
    return region



def _search_region_cropping_is_enabled(job_properties):
    return utils.get_property(job_properties, 'SEARCH_REGION_ENABLE_DETECTION', False)

def _feed_forward_exact_region_is_enabled(job_properties: Mapping[str, str]) -> bool:
    ff_type = job_properties.get('FEED_FORWARD_TYPE')
    return 'REGION' == ff_type.upper() if ff_type else False

def _feed_forward_superset_region_is_enabled(job_properties: Mapping[str, str]) -> bool:
    ff_type = job_properties.get('FEED_FORWARD_TYPE')
    return 'SUPERSET_REGION' == ff_type.upper() if ff_type else False


def _feed_forward_is_enabled(job_properties: Mapping[str, str]) -> bool:
    return _feed_forward_superset_region_is_enabled(job_properties) \
           or _feed_forward_exact_region_is_enabled(job_properties)


def _get_fill_color(job_properties: Mapping[str, str]) -> Tuple[int, int, int]:
    fill_color_name = job_properties.get('ROTATION_FILL_COLOR')
    if not fill_color_name:
        return (0, 0, 0)

    fill_color_name = fill_color_name.upper()
    if fill_color_name == 'BLACK':
        return (0, 0, 0)
    elif fill_color_name == 'WHITE':
        return (255, 255, 255)
    else:
        raise mpf.DetectionError.INVALID_PROPERTY.exception(
            'Expected the "ROTATION_FILL_COLOR" property to be either "BLACK" or "WHITE", '
            f'but it was set to "{fill_color_name}".')


def _get_search_region(job_properties):
    if not _search_region_cropping_is_enabled(job_properties):
        return SearchRegion()

    return SearchRegion(
        _get_region_edge(job_properties, 'SEARCH_REGION_TOP_LEFT_X_DETECTION'),
        _get_region_edge(job_properties, 'SEARCH_REGION_TOP_LEFT_Y_DETECTION'),
        _get_region_edge(job_properties, 'SEARCH_REGION_BOTTOM_RIGHT_X_DETECTION'),
        _get_region_edge(job_properties, 'SEARCH_REGION_BOTTOM_RIGHT_Y_DETECTION'))


def _get_region_edge(props, prop_name):
    try:
        prop_val = props.get(prop_name, '-1')
        percent_idx = prop_val.find('%')
        if percent_idx >= 0:
            return RegionEdge.percentage(float(prop_val[:percent_idx]))
        return RegionEdge.absolute(int(prop_val))
    except ValueError:
        # Failed to convert property to number.
        return RegionEdge.default()

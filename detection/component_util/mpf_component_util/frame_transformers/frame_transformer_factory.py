from . import frame_transformer, frame_rotator, frame_flipper, frame_cropper
from .. import utils


def get_transformer(job, input_frame_size):
    if hasattr(job, 'feed_forward_track'):
        ff_track = job.feed_forward_track
    elif hasattr(job, 'feed_forward_location'):
        ff_track = {0: job.feed_forward_location}
    else:
        ff_track = dict()
    return _get_transformer(job, input_frame_size, ff_track)



def _get_transformer(job, input_frame_size, feed_forward_track):
    transformer = frame_transformer.NoOpTransformer(input_frame_size)

    transformer = _add_rotator_if_needed(job.job_properties, job.media_properties, transformer)
    transformer = _add_flipper_if_needed(job.job_properties, job.media_properties, transformer)
    transformer = _add_cropper_if_needed(job, input_frame_size, feed_forward_track, transformer)

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


def _add_cropper_if_needed(job, input_frame_size, feed_forward_track, current_transformer):
    exact_region_enabled = 'REGION' == job.job_properties.get('FEED_FORWARD_TYPE', '').upper()
    superset_region_enabled = 'SUPERSET_REGION' == job.job_properties.get('FEED_FORWARD_TYPE', '').upper()
    search_region_enabled = utils.get_property(job.job_properties, 'SEARCH_REGION_ENABLE_DETECTION', False)

    if not exact_region_enabled and not superset_region_enabled and not search_region_enabled:
        return current_transformer

    if exact_region_enabled:
        return frame_cropper.FeedForwardFrameCropper(current_transformer, feed_forward_track)

    if superset_region_enabled:
        region_of_interest = _get_superset_region(feed_forward_track)
    else:
        region_of_interest = _get_search_region(job.job_properties, input_frame_size)

    region_is_entire_frame = region_of_interest == utils.Rect(0, 0, *input_frame_size)

    if region_is_entire_frame:
        return current_transformer
    else:
        return frame_cropper.SearchRegionFrameCropper(current_transformer, region_of_interest)



def _get_superset_region(feed_forward_track):
    if not feed_forward_track:
        raise IndexError('FEED_FORWARD_TYPE: SUPERSET_REGION is enabled, but feed forward track was empty.')

    image_location_iter = feed_forward_track.itervalues()
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


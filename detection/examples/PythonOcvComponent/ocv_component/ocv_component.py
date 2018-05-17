import cv2
import mpf_component_api as mpf


logger = mpf.configure_logging('python-ocv-test.log', __name__ == '__main__')


class OcvComponent(object):
    detection_type = 'PYTHON OCV TEST'


    @staticmethod
    def get_detections_from_image(image_job):
        logger.info('[%s] Received image job: %s', image_job.job_name, image_job)

        img = cv2.imread(image_job.data_uri)

        height, width, _ = img.shape
        logger.info('[%s] Image at %s: width = %s, height = %s', image_job.job_name, image_job.data_uri, width, height)

        detection_sz = 10
        yield mpf.ImageLocation(0, height / 2 - detection_sz, width - 1, detection_sz, -1.0,
                                mpf.Properties(METADATA='full_width'))

        yield mpf.ImageLocation(width / 2 - detection_sz, 0, detection_sz, height - 1, -1.0,
                                mpf.Properties(METADATA='full_height'))


    @staticmethod
    def get_detections_from_video(video_job):
        logger.info('[%s] Received video job: %s', video_job.job_name, video_job)

        video_cap = cv2.VideoCapture(video_job.data_uri)
        height = video_cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        width = video_cap.get(cv2.CAP_PROP_FRAME_WIDTH)

        start_frame = video_job.start_frame
        stop_frame = video_job.stop_frame

        detections = mpf.FrameLocationMap()
        last_il = mpf.ImageLocation(width / 2 - 1, height / 2 - 1, 2, 2)
        last_frame_read = 0
        for idx in xrange(start_frame, stop_frame + 1):
            was_read, frame = video_cap.read()
            if not was_read:
                break
            last_frame_read = idx
            last_il = mpf.ImageLocation(
                max(0, last_il.x_left_upper - 1),
                max(0, last_il.y_left_upper - 1),
                min(width - 1, last_il.width + 2),
                min(height - 1, last_il.height + 2))
            detections[idx] = last_il

        if not detections:
            return ()
        return [mpf.VideoTrack(start_frame, last_frame_read, -1, detections)]

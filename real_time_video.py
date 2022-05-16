from keras.preprocessing.image import img_to_array
import imutils
import cv2
from keras.models import load_model
import numpy as np
from gaze_tracking import GazeTracking

# 함수명 : test_start
# 기능 : 전체 분석을 시작하기 위한 함수
# 작성일자 : 2022/05/08


def test_start():
    # 데이터와 이미지를 로딩하기 위한 매개변수들
    detection_model_path = 'haarcascade_files/haarcascade_frontalface_default.xml'
    emotion_model_path = 'models/_mini_XCEPTION.102-0.66.hdf5'

    # 박스의 모양을 바운딩하기 위한 매개변수들
    # 모델 로딩
    face_detection = cv2.CascadeClassifier(detection_model_path)
    emotion_classifier = load_model(emotion_model_path, compile=False)
    EMOTIONS = ["angry", "disgust", "scared", "happy", "sad", "surprised",
                "neutral"]
    emotionScore = [0] * 7

    testFlag = 1
    emotionVal = 0
    gazeVal = 0

    # 비디오 스트리밍 시작
    cv2.namedWindow('your_face')
    gaze = GazeTracking()
    camera = cv2.VideoCapture(0)
    while True:
        frame = camera.read()[1]
        gaze.refresh(frame)
        frame = gaze.annotated_frame()
        text = ""
        if gaze.is_right():
            gaze.GazeScore["right"] += 1
            text = "right"
            gazeVal += 1
        elif gaze.is_left():
            gaze.GazeScore["left"] += 1
            text = "left"
            gazeVal += 1
        elif gaze.is_blinking():
            gaze.GazeScore["blinking"] += 1
            text = "blinking"
            gazeVal += 1
        elif gaze.is_center():
            gaze.GazeScore["center"] += 1
            text = "Looking center"
            gazeVal += 1
        cv2.putText(frame, text, (90, 60),
                    cv2.FONT_HERSHEY_DUPLEX, 1.6, (147, 58, 31), 2)
        left_pupil = gaze.pupil_left_coords()
        right_pupil = gaze.pupil_right_coords()
        # cv2.putText(frame, "Left pupil:  " + str(left_pupil), (90, 130),
        #           cv2.FONT_HERSHEY_DUPLEX, 0.9, (147, 58, 31), 1)
        # cv2.putText(frame, "Right pupil: " + str(right_pupil), (90, 165),
        #           cv2.FONT_HERSHEY_DUPLEX, 0.9, (147, 58, 31), 1)

        # 프레임을 읽어낸다
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_detection.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30), flags=cv2.CASCADE_SCALE_IMAGE)

        canvas = np.zeros((250, 300, 3), dtype="uint8")
        frameClone = frame.copy()
        if len(faces) > 0:
            faces = sorted(faces, reverse=True,
                           key=lambda x: (x[2] - x[0]) * (x[3] - x[1]))[0]
            (fX, fY, fW, fH) = faces

            # CNN 분류를 위한 ROI 추출
            roi = gray[fY:fY + fH, fX:fX + fW]
            roi = cv2.resize(roi, (64, 64))
            roi = roi.astype("float") / 255.0
            roi = img_to_array(roi)
            roi = np.expand_dims(roi, axis=0)

            preds = emotion_classifier.predict(roi)[0]
            emotion_probability = np.max(preds)
            label = EMOTIONS[preds.argmax()]
            emotionScore[preds.argmax()] += 1
            emotionVal += 1

        else:
            continue

        for (i, (emotion, prob)) in enumerate(zip(EMOTIONS, preds)):
            # 라벨링 텍스트를 만든다
            text = "{}: {:.2f}%".format(emotion, prob * 100)

            # 화면에 라벨과 확률 바를 그린다
            w = int(prob * 300)
            cv2.rectangle(canvas, (7, (i * 35) + 5),
                          (w, (i * 35) + 35), (0, 0, 255), -1)
            cv2.putText(canvas, text, (10, (i * 35) + 23),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                        (255, 255, 255), 2)
            cv2.putText(frameClone, label, (fX, fY - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 2)
            cv2.rectangle(frameClone, (fX, fY), (fX + fW, fY + fH),
                          (0, 0, 255), 2)

        cv2.imshow('your_face', frameClone)
        #cv2.imshow("Probabilities", canvas)
        if cv2.waitKey(1) & 0xFF == ord('q'):  # 삭제 시 실행 X
            break

        if testFlag == 1:
            if emotionVal >= 50:
                print(emotionScore)
                if ((emotionScore[0] + emotionScore[1] + emotionScore[2] + emotionScore[4] + emotionScore[5] + emotionScore[6]) * 0.8 >= emotionScore[3]):
                    print("Negative")
                else:
                    print("positive")
                emotionVal = 0
                for i in range(7):
                    emotionScore[i] = 0
            if gazeVal >= 50:
                print(gaze.GazeScore)
                gaze.GazeScore["blinking"] = 0
                gaze.GazeScore["right"] = 0
                gaze.GazeScore["left"] = 0
                gaze.GazeScore["center"] = 0
                gazeVal = 0

    camera.release()
    cv2.destroyAllWindows()


test_start()

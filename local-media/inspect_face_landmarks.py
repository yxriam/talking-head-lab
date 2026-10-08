import cv2
from insightface.app import FaceAnalysis

app = FaceAnalysis(name='antelopev2', root='/opt/media-models/InstantID', providers=['CPUExecutionProvider'])
app.prepare(ctx_id=-1, det_size=(640, 640))
cap = cv2.VideoCapture('/mnt/d/project/NZ/cv/benchmark-results/2026-09-23-equal-input/joyvasa/output.mp4')
ok, frame = cap.read()
face = max(app.get(frame), key=lambda item: item.bbox[2] - item.bbox[0])
print(face.keys())
for key in face.keys():
    value = face[key]
    print(key, getattr(value, 'shape', None))

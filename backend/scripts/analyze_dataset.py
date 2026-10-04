import argparse
import re
from pathlib import Path
import yaml

repository_root = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description='Count YOLO class support by dataset split.')
parser.add_argument(
    '--dataset',
    type=Path,
    default=repository_root / 'krough' / 'labels.v6i.yolov8',
    help='Extracted YOLO dataset directory.',
)
root = parser.parse_args().dataset
with open(root / 'data.yaml', encoding='utf-8') as fh:
    data = yaml.safe_load(fh)

names = data.get('names', [])
if isinstance(names, dict):
    names = [names.get(index, names.get(str(index), str(index))) for index in range(data.get('nc', len(names)))]
print('nc=', data.get('nc', len(names)))
print('class names=', names)
capture_frames = []
for split in ['train', 'valid', 'test']:
    files = sorted((root / split / 'labels').glob('*.txt'))
    for image_path in (root / split / 'images').glob('*'):
        match = re.match(
            r'^(?P<session>.+?)_(?P<hour>\d{2})_(?P<minute>\d{2})_(?P<second>\d{2})_(?P<millisecond>\d{3})_png',
            image_path.name,
        )
        if match:
            timestamp = (
                int(match['hour']) * 3600
                + int(match['minute']) * 60
                + int(match['second'])
                + int(match['millisecond']) / 1000
            )
            capture_frames.append((match['session'], timestamp, split, image_path.name))
    counts = {}
    image_support = {}
    for path in files:
        classes_in_image = set()
        for line in path.read_text(encoding='utf-8').splitlines():
            if not line.strip():
                continue
            cls = int(line.split()[0])
            counts[cls] = counts.get(cls, 0) + 1
            classes_in_image.add(cls)
        for cls in classes_in_image:
            image_support[cls] = image_support.get(cls, 0) + 1
    print(f'\n{split}: {len(files)} label files, {sum(counts.values())} objects, {len(counts)} observed classes')
    supports = [image_support.get(cls, 0) for cls in range(len(names))]
    nonzero_supports = [support for support in supports if support]
    print(
        'support bands:',
        f'0={sum(support == 0 for support in supports)}',
        f'1-4={sum(1 <= support <= 4 for support in supports)}',
        f'5-9={sum(5 <= support <= 9 for support in supports)}',
        f'10+={sum(support >= 10 for support in supports)}',
        f'min_nonzero={min(nonzero_supports) if nonzero_supports else 0}',
        f'max={max(supports, default=0)}',
    )
    print('classes below 5 images:', [(names[cls], support) for cls, support in enumerate(supports) if support < 5])
    for cls in range(len(names)):
        print(f'{cls:02d}\t{names[cls]}\tobjects={counts.get(cls, 0)}\timages={image_support.get(cls, 0)}')

capture_frames.sort()
capture_bursts = []
for frame in capture_frames:
    if (
        not capture_bursts
        or frame[0] != capture_bursts[-1][-1][0]
        or frame[1] - capture_bursts[-1][-1][1] > 2
    ):
        capture_bursts.append([frame])
    else:
        capture_bursts[-1].append(frame)
cross_split_bursts = [
    burst for burst in capture_bursts if len({frame[2] for frame in burst}) > 1
]
print(
    '\nCapture bursts (<=2s gaps):',
    len(capture_bursts),
    'crossing splits:',
    len(cross_split_bursts),
    'images in cross-split bursts:',
    sum(len(burst) for burst in cross_split_bursts),
)
for burst in cross_split_bursts[:10]:
    splits = sorted({frame[2] for frame in burst})
    print('cross-split burst:', splits, [frame[3] for frame in burst])

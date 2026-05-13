# /// script
# dependencies = [
#     "marimo",
#     "librosa==0.11.0",
#     "numpy==2.4.4",
#     "scikit-image==0.26.0",
#     "scipy==1.17.1",
#     "yt-dlp[default]==2026.3.17",
#     "matplotlib==3.10.9",
# ]
# requires-python = ">=3.14"
# ///

import marimo

__generated_with = "0.23.6"
app = marimo.App(width="medium")

with app.setup(hide_code=True):
    import marimo as mo

    import numpy as np
    import scipy
    import skimage

    from pathlib import Path
    import librosa  # to read & process .wav audios
    import librosa.display  # to display spectogram
    import yt_dlp  # to download YouTube Music

    import tempfile
    import subprocess
    import random


    MAGIC_NUMBER = np.float32(44100 / 512)


    print = mo.output.append


    def input(lbl=""):
        input_text = mo.ui.text(label=lbl)
        print(input_text)
        return input_text


@app.function
def download_music(url_path="public/shazam/train.url"):
    urls = [
        url
        for url in Path(url_path).read_text().splitlines()
        if url.strip() and not url.strip().startswith("#")
    ]

    ydl_opts = {
        "format": "wav/bestaudio/best",
        "download_archive": "public/shazam/archive.txt",
        "paths": {"home": "public/shazam/", "temp": "tmp"},
        "writesubtitles": True,
        "writethumbnail": True,
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "wav"},
            {
                "key": "FFmpegThumbnailsConvertor",
                "when": "before_dl",
                "format": "png",
            },
            {
                "key": "FFmpegMetadata",
                "add_chapters": True,
                "add_infojson": "if_exists",
                "add_metadata": True,
            },
            {
                "key": "FFmpegConcat",
                "only_multi_video": True,
                "when": "playlist",
            },
        ],
        "outtmpl": {
            "default": "wav/%(id)s.%(ext)s",
            "subtitle": "sub/%(id)s.%(ext)s",
            "thumbnail": "thumbnail/%(id)s.%(ext)s",
        },
    }

    # download music as wav
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        error_code = ydl.download(urls)


@app.function
def get_spectogram(y):
    return librosa.amplitude_to_db(np.abs(librosa.stft(y)), ref=np.max)


@app.function
def show_spectogram(S_db, sr=44100):
    return librosa.display.specshow(S_db, sr=sr)


@app.function
def all_local_maxima(arr, min_dist=7, sigma=0):
    return skimage.feature.peak_local_max(arr, min_distance=min_dist)


@app.function
def coords2consmap(coords, shape):
    cons_map = np.zeros(shape)
    cons_map[coords[:, 0], coords[:, 1]] = 1
    return cons_map


@app.function
def both_fc(x):
    return coords2consmap(all_local_maxima(x), x.shape)


@app.function
def serialize(f1, f2, t1, t2):
    "return f1:f2:t2-t1, t1"

    f1 = f1.astype(np.uint32)
    f2 = f2.astype(np.uint32)
    t1 = t1.astype(np.uint32)
    t2 = t2.astype(np.uint32)

    return (f1 << 22) + (f2 << 12) + (t2 - t1), np.full_like(t2, t1)


@app.function
def deserialize(hash, t1):
    "return f1, f2, t1, t2"
    return (
        (hash & 0xFFC00000) >> 22,
        (hash & 0x3FF000) >> 12,
        t1,
        t1 + (hash & 0xFFF),
    )


@app.function
def get_hashes(spectogram, freq_thresh=20, time_thresh=50):
    anchors_test = all_local_maxima(spectogram)
    hashes = []

    for anchor in anchors_test:
        mask = (
            (anchor[1] < anchors_test[:, 1])
            & (anchors_test[:, 1] <= anchor[1] + time_thresh)
            & (anchor[0] - freq_thresh <= anchors_test[:, 0])
            & (anchors_test[:, 0] <= anchor[0] + freq_thresh)
        )

        neighbors = anchors_test[mask]

        hashes.append(
            serialize(
                np.uint32(anchor[0]),
                neighbors[:, 0],
                np.uint32(anchor[1]),
                neighbors[:, 1],
            )
        )

    hashes = np.hstack(hashes)
    idx_sorted = np.argsort(hashes[0])

    return np.vstack((hashes[0][idx_sorted], hashes[1][idx_sorted]))


@app.function
def get_hist(hashes, hashes_test):
    xy, x_idx, y_idx = np.intersect1d(
        hashes[0], hashes_test[0], return_indices=True
    )

    offsets = hashes[:, x_idx][1] - hashes_test[:, y_idx][1]
    # remove negative values that overshoots int32 range when converted to uint32
    offsets = offsets[offsets <= np.iinfo(np.int32).max]

    if len(offsets) == 0:
        mmax = 2 * MAGIC_NUMBER
    else:
        mmax = offsets.max()

    n_bins = int(1 + (mmax // MAGIC_NUMBER))

    return np.histogram(offsets, bins=n_bins, range=(0, n_bins * MAGIC_NUMBER))


@app.function
def gen_test_samples(n_samples=5, sample_times=(5, 10, 15)):
    cmd = ""

    for rec_path in Path("public/shazam/test_rec/").glob("*.wav"):
        for sample_time in sample_times:
            for _ in range(n_samples):
                rec_duration = round(librosa.get_duration(path=rec_path)) - 2
                start = random.randint(0, rec_duration - sample_time)
                end = start + sample_time

                cmd += f"ffmpeg -i public/shazam/test_rec/{rec_path.stem}.wav -ss 00:{start // 60:02}:{start % 60:02} -to 00:{end // 60:02}:{end % 60:02} public/shazam/test_samples/{rec_path.stem}.{sample_time:02}.{start:03}.wav -y\n"

    return mo.ui.code_editor(cmd)


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Testing code
    """)
    return


@app.cell
def _():
    # mo.hstack(["Upload", switch, "Record"], justify="center")
    return


@app.cell
def _():
    # if switch.value:
    #     print(mo.hstack([microphone, mo.audio(microphone.value)]))
    # else:
    #     print(file)
    return


@app.cell
def _():
    # pipeline()
    return


@app.function
def get_test_score(matches, url_magic):
    score_y, score_n = 0, 0
    score_y += matches[0]["highest_peak"]

    if matches[1]["url_magic"] == url_magic:
        score_y += matches[1]["highest_peak"]
    else:
        score_n += matches[1]["highest_peak"]

    if matches[2]["url_magic"] == url_magic:
        score_y += matches[2]["highest_peak"]
    else:
        score_n += matches[2]["highest_peak"]

    return score_y, score_n


@app.cell
def _(get_best_match):
    def ftest_shazam():
        n_matches = {0: [], 1: [], 2: [], "no": []}
        scores_y = {0: 0, 1: 0, 2: 0, 3: 0}
        scores_n = {0: 0, 1: 0, 2: 0, 3: 0}

        for sample_path in mo.status.progress_bar(
            list(Path("public/shazam/test_samples/").glob("*.wav")),
            title="Testing Sample Clips...",
            completion_title="All Sample Clips Tested...",
            show_eta=True,
            show_rate=True,
        ):
            matches = get_best_match(sample_path)
            url_magic, duration, start = sample_path.stem.split(".")

            if matches[0]["url_magic"] == url_magic:
                n_matches[0].append(sample_path)
                score_y, score_n = get_test_score(matches, url_magic)
                scores_y[0] += score_y
                scores_n[0] += score_n

            elif matches[1]["url_magic"] == url_magic:
                n_matches[1].append(sample_path)
                score_y, score_n = get_test_score(matches, url_magic)
                scores_y[1] += score_y
                scores_n[1] += score_n

            elif matches[2]["url_magic"] == url_magic:
                n_matches[2].append(sample_path)
                score_y, score_n = get_test_score(matches, url_magic)
                scores_y[2] += score_y
                scores_n[2] += score_n

            else:
                n_matches["no"].append(sample_path)
                score_y, score_n = get_test_score(matches, "")
                scores_y[3] += score_y
                scores_n[3] += score_n

            # mo.output.replace((scores_y, scores_n,n_matches))
            mo.output.replace_at_index((scores_y, scores_n, n_matches), 1)

    return


@app.cell
def _():
    # ftest_shazam()
    return


@app.cell
def _():
    # gen_test_samples()
    return


if __name__ == "__main__":
    app.run()

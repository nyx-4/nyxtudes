# /// script
# dependencies = [
#     "librosa==0.11.0",
#     "marimo",
#     "matplotlib==3.10.9",
#     "numpy==2.4.4",
#     "scikit-image==0.26.0",
#     "yt-dlp==2026.3.17",
# ]
# requires-python = ">=3.14"
# ///

import marimo

__generated_with = "0.23.6"
app = marimo.App(width="medium")

with app.setup(hide_code=True):
    import marimo as mo
    import shazam_helper

    import numpy as np
    import librosa
    import yt_dlp
    from pathlib import Path
    from heapq import nlargest
    import tempfile
    import subprocess

    microphone = mo.ui.microphone(label="Drop a beat!")
    file = mo.ui.file_browser(
        label="Upload .wav recording!",
        filetypes=[".wav"],
        multiple=False,
        ignore_empty_dirs=True,
    )
    switch = mo.ui.switch()

    print = mo.output.append


    def input(lbl=""):
        input_text = mo.ui.text(label=lbl)
        print(input_text)
        return input_text


@app.cell
def _():
    mo.hstack(["Upload", switch, "Record"], justify="center")
    return


@app.cell
def _():
    if switch.value:
        print(
            mo.hstack(
                [
                    microphone,
                    mo.audio(microphone.value),
                ]
            )
        )
    else:
        print(file)
    return


@app.cell
def _():
    scores = pipeline()

    mo.output.clear()
    # scores
    return (scores,)


@app.cell
def _(scores):
    mo.vstack(
        [
            mo.md("# Top Match"),
            mo.Html(f"""<a href='{scores[0]["youtube"]}'>
                    {
                mo.image(
                    src=scores[0]["thumbnail"],
                    alt=scores[0]["youtube"],
                    width=900,
                    rounded=True,
                    caption=scores[0]["youtube"]
                    + f" (Score: {scores[0]['highest_peak']})",
                ).text
            }</a>"""),
            mo.md("# Next Two Candidates"),
            mo.hstack(
                [
                    mo.Html(f"""<a href='{scores[1]["youtube"]}'>
                    {
                        mo.image(
                            src=scores[1]["thumbnail"],
                            alt=scores[1]["youtube"],
                            width=440,
                            rounded=True,
                            caption=scores[1]["youtube"]
                            + f" (Score: {scores[1]['highest_peak']})",
                        ).text
                    }</a>"""),
                    mo.Html(f"""<a href='{scores[2]["youtube"]}'>
                    {
                        mo.image(
                            src=scores[2]["thumbnail"],
                            alt=scores[2]["youtube"],
                            width=440,
                            rounded=True,
                            caption=scores[2]["youtube"]
                            + f" (Score: {scores[2]['highest_peak']})",
                        ).text
                    }</a>"""),
                ],
                align="center",
            ),
        ],
        align="center",
    )
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Helper functions
    """)
    return


@app.function(hide_code=True)
def get_test_audio(path=None):
    if path is not None:
        return librosa.load(path, sr=44100)

    if switch.value is False:  # uploaded .wav file
        return librosa.load(file.path(), sr=44100)

    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f_in:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f_out:
            f_in.write(microphone.value.read())
            f_in.flush()

            try:
                subprocess.run(
                    [
                        "ffmpeg",
                        "-i",
                        f_in.name,
                        "-ar",
                        "44100",
                        "-f",
                        "wav",
                        f_out.name,
                        "-y",
                    ],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except subprocess.CalledProcessError:
                raise ValueError(
                    "No audio segment detected! Please, record audio..."
                )

            return librosa.load(f_out.name, sr=44100)


@app.function(hide_code=True)
def get_best_match(path=None):
    y_test, _ = get_test_audio(path)
    hashes_test = shazam_helper.get_hashes(
        shazam_helper.get_spectogram(y_test)
    )
    scores = []

    for npy_path in Path("public/shazam/npy").glob("*.npy"):
        hashes = np.load(npy_path)
        hist, bin_edges = shazam_helper.get_hist(hashes, hashes_test)

        if len(hist) == 0:  # empty: do nothing
            continue
        elif len(hist) == 1:  # 1 element: select only that
            max2, max1 = 0, hist[0]
            time1 = int(bin_edges[max1] // shazam_helper.MAGIC_NUMBER)
            time2 = 0
        else:  # >=2 elements: select top 2
            max2, max1 = np.argsort(hist)[-2:]
            time1 = int(bin_edges[max1] // shazam_helper.MAGIC_NUMBER)
            time2 = int(bin_edges[max2] // shazam_helper.MAGIC_NUMBER)

        scores.append(  # append largest
            {
                "url_magic": npy_path.stem,
                "highest_peak": hist[max1],
                "start_time": time1,
                "thumbnail": f"public/shazam/thumbnail/{npy_path.stem}.png",
                "youtube": f"https://www.youtube.com/watch?v={npy_path.stem}&t={time1}",
            }
        )

        scores.append(  # append 2nd largest
            {
                "url_magic": npy_path.stem,
                "highest_peak": hist[max2],
                "start_time": time2,
                "thumbnail": f"public/shazam/thumbnail/{npy_path.stem}.png",
                "youtube": f"https://www.youtube.com/watch?v={npy_path.stem}&t={time2}",
            }
        )

    return nlargest(3, scores, key=lambda d: d["highest_peak"])


@app.function(hide_code=True)
def pipeline():
    subdir = Path("public/shazam/")
    # with mo.status.spinner(title="Downloading...") as _:
    # shazam_helper.download_music()

    # generate hashes dataset in 'public/shazam/npy'
    for wav_path in mo.status.progress_bar(
        list((subdir / "wav").glob("*.wav")),
        title="Generaing Combinatorial Hashes...",
        completion_title="All Combinatorial Hashes Created...",
        show_eta=True,
        show_rate=True,
    ):
        # calculate hashes, if NOT already computed
        npy_path = Path(f"public/shazam/npy/{wav_path.stem}.npy")
        if not npy_path.exists():
            y, _ = librosa.load(wav_path, sr=44100)
            hashes = shazam_helper.get_hashes(shazam_helper.get_spectogram(y))
            np.save(file=npy_path, arr=hashes)

    scores = get_best_match()

    return scores


if __name__ == "__main__":
    app.run()

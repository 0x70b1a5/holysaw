import { PlayOptions, playSong } from '../utils/play'

self.onmessage = function(e: { data: PlayOptions }) {
  const { song, parser, name: songName, preamble, playAudio, saveAsWav, audioContext, setAnalyserNode } = e.data;

  try {
    // Assuming playSong is exposed correctly after the importScripts
    const result = playSong({
      song,
      parser,
      name: songName,
      preamble,
      playAudio,
      saveAsWav,
      audioContext,
      setAnalyserNode
    });

    // Post the result back to the main thread
    self.postMessage({ action: 'songProcessed', result });
  } catch (error) {
    // Post any error back to the main thread
    self.postMessage({ action: 'error', error });
  }
}

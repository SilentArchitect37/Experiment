// EmulatorJS (mGBA core) is loaded from its CDN at a pinned version. To play fully offline,
// download https://cdn.emulatorjs.org/4.2.3/data/ into ./vendor/emulatorjs/ and point this there.
export const EMULATORJS_DATA = 'https://cdn.emulatorjs.org/4.2.3/data/';

export const FILTERS = {
  hd4x:   { label: 'HD Smooth (4× ScaleHQ)', shader: '4xScaleHQ.glslp' },
  hd2x:   { label: 'HD Soft (2× ScaleHQ)',   shader: '2xScaleHQ.glslp' },
  crt:    { label: 'Retro CRT',              shader: 'crt-easymode.glslp' },
  sharp:  { label: 'Original pixels',        shader: 'disabled' },
};
export const DEFAULT_FILTER = 'hd4x';

(function () {
  'use strict';

  function removeLicenseFromJson(source) {
    const document = JSON.parse(source);

    if (document.info) {
      delete document.info.license;
    }

    return document;
  }

  function removeLicenseFromYaml(source) {
    const lines = source.split(/\r?\n/);
    const output = [];
    let insideInfo = false;
    let skippingLicense = false;

    for (const line of lines) {
      if (/^info:\s*(?:#.*)?$/.test(line)) {
        insideInfo = true;
        skippingLicense = false;
        output.push(line);
        continue;
      }

      if (insideInfo && /^\S/.test(line) && line.trim() !== '') {
        insideInfo = false;
        skippingLicense = false;
      }

      if (insideInfo && /^  license:\s*(?:#.*)?$/.test(line)) {
        skippingLicense = true;
        continue;
      }

      if (skippingLicense) {
        if (/^  \S/.test(line)) {
          skippingLicense = false;
        } else {
          continue;
        }
      }

      output.push(line);
    }

    return output.join('\n');
  }

  async function create(selector, specUrl, options) {
    const response = await fetch(specUrl);

    if (!response.ok) {
      throw new Error(`Unable to load OpenAPI contract (${response.status})`);
    }

    const source = await response.text();
    const content = source.trimStart().startsWith('{')
      ? removeLicenseFromJson(source)
      : removeLicenseFromYaml(source);

    return Scalar.createApiReference(selector, {
      ...options,
      content
    });
  }

  window.SmartTouchPlayground = { create };
})();

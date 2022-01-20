# RUN: %PYTHON %s

import absl.testing
import numpy
import test_util

model_path = "https://storage.googleapis.com/iree-model-artifacts/ssd_mobilenet_v1_320_1.0_float.tflite"

class SsdMobilenetV1Test(test_util.TFLiteModelTest):
  def __init__(self, *args, **kwargs):
    super(SsdMobilenetV1Test, self).__init__(model_path, *args, **kwargs)

  def compare_results(self, iree_results, tflite_results, details):
    super(SsdMobilenetV1Test, self).compare_results(iree_results, tflite_results, details)
    for i in range(len(iree_results)):
      self.assertTrue(numpy.isclose(iree_results[i], tflite_results[i], atol=1e-4).all())

  def test_compile_tflite(self):
    self.compile_and_execute()

if __name__ == '__main__':
  absl.testing.absltest.main()

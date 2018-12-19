# Zero-Shot-Style-Transfer

This repository contains code and data for some earlier work on a project which was published with a different title reflecting major changes to the work's direction.  The paper can be found at https://royalsocietypublishing.org/doi/full/10.1098/rsos.171920 and the repository associated with that work can be found at https://github.com/keithecarlson/StyleTransferBibleData.

I have left this version, but you should check out the other project as well.  Any citations should be to the Royal Society paper.

To run the experiment described below you will need to first install Tensorflow 1.1(https://pypi.python.org/pypi/tensorflow/1.1.0), MOSES (http://www.statmt.org/moses/index.php?n=Main.HomePage), and seq2seq (https://github.com/google/seq2seq).  We also use subword-nmt (https://github.com/rsennrich/subword-nmt), but the code is replicated within this repository.

Once you have the prerequsites installed and have cloned this repository you are ready to start.  In the paper we use 33 versions of the Bible, but only 6 of them are available in the public domain.  we will reproduce a smaller version of our experiment in this short tutorial.  We will train a model to translate from 'ASV' to 'BBE' despite never having seen any examples of this source->target pair.

Begin by opening createSample.py in the Scripts/createSamples directory and changing repositoryDir at the top of the file to point to your local repository.  You can now run this file which will produce a new directory "Sample" inside the Data directory.  It contains test, development, and training samples formatted for both MOSES and Seq2Seq.

To train Moses, first create a directory within Zero-Shot-Style-Transfer called mosesBibleStyle.  Next open config.exp in Scripts/trainMoses and change repository-dir as above.  Now you are ready to start training the model with the command (changing the path to experiment.perl if needed).  From the mosesBibleStyle directory run:

```
~/mosesdecoder/scripts/ems/experiment.perl -config ../Scripts/trainMoses/config.exp -exec
```

This will eventually produce some output which we will look at later.

To train seq2seq, first set the path to this repository with a command like

```
export REPO_DIR=/home/kcarlson/Zero-Shot-Style-Transfer/
```

Then create a directory called seq2SeqBibleStyle within the repository.  Start the training with

```
export MODEL_DIR=${REPO_DIR}/seq2SeqBibleStyle/

python -m bin.train \
  --config_paths="
      ${REPO_DIR}/Scripts/trainSeq2Seq/ourConfig.yml,
      ${REPO_DIR}/Scripts/trainSeq2Seq/ourTrainSeq2Seq.yml" \
  --model_params "
      vocab_source: ${REPO_DIR}/Data/Vocab/vocabClean.txt
      vocab_target: ${REPO_DIR}/Data/Vocab/vocabClean.txt" \
  --input_pipeline_train "
    class: ParallelTextInputPipeline
    params:
      shuffle: True
      source_files:
        - ${REPO_DIR}/Data/Sample/Seq2SeqSamples/train.sourc
      target_files:
        - ${REPO_DIR}/Data/Sample/Seq2SeqSamples/train.tgt" \
  --input_pipeline_dev "
    class: ParallelTextInputPipeline
    params:
       source_files:
        - ${REPO_DIR}/Data/Sample/Seq2SeqSamples/dev.sourc
       target_files:
        - ${REPO_DIR}/Data/Sample/Seq2SeqSamples/dev.sourc" \
  --batch_size 64 \
  --train_steps 500000 \
  --keep_checkpoint_max 0 \
  --save_checkpoints_steps 5000 \
  --schedule train \
  --output_dir $MODEL_DIR \   
```

This training may take several days on a GPU.  Checkpoints will be saved every 5000 steps and you can use these checkpoints to decode.  For example, to decode using checkpoint 330001:

```

export MODEL_DIR=${REPO_DIR}/seq2SeqBibleStyle/
export PRED_DIR=${MODEL_DIR}/decodingResults/testOutCheckpoint330001
mkdir -p ${PRED_DIR}
  
python -m bin.infer \
  --tasks "
    - class: DecodeText
    - class: DumpBeams
      params:
        file: ${PRED_DIR}/beams.npz" \
  --model_dir $MODEL_DIR \
  --checkpoint_path ${REPO_DIR}/seq2SeqBibleStyle/model.ckpt-330001 \
  --model_params "
    inference.beam_search.beam_width: 10" \
  --input_pipeline "
    class: ParallelTextInputPipeline
    params:
      source_files:
       - ${REPO_DIR}/Data/Sample/Seq2SeqSamples/test.sourc" \
  > ${PRED_DIR}/predictions.txt
  
```

The output from decoding with seq2seq will likely contain some subword units.  To replace these and get more natural looking text use

```
sed -i 's/@@ //g' ${PRED_DIR}/predictions.txt
```

You should now have the output of seq2seq checkpoints that you've decoded in seq2SeqBibleStyle/decodingResults and the output of Moses in mosesBibleStyle/evaluation/Test.cleaned.1.  You can evaluate these outputs with the PINC and BLEU metrics. These scripts are originally from Moses and I've taken from (https://github.com/harsh19/Shakespearizing-Modern-English) and included in the Scripts/evaluation directory.  To see how closely moses output resembles the target output use:

```
perl Scripts/evaluate/multi-bleu.perl Data/Sample/MosesSamples/test.tgt < mosesBibleStyle/evaluation/Test.cleaned.1
```

Note that this cleaned output will be followed by "1" only if the training was completed the first time the command was issued.  Be sure to use the final output if there were multiple steps run.  For for the seq2seq output:

```
perl Scripts/evaluate/multi-bleu.perl Data/Sample/MosesSamples/test.tgt <  ${PRED_DIR}/predictions.txt
```

To see how distant they are from the source sentence (PINC) use:

```
perl Scripts/evaluate/PINC.perl Data/Sample/MosesSamples/test.sourc <  mosesBibleStyle/evaluation/Test.cleaned.1
```

or:

```
perl Scripts/evaluate/PINC.perl Data/Sample/MosesSamples/test.sourc <  ${PRED_DIR}/predictions.txt
```

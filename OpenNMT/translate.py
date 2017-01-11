import onmt.init

parser = argparse.ArgumentParser(description='translate.py')

parser.add_argument('-model', required=True, help="Path to model .pt file")
parser.add_argument('-src',   required=True, help="Source sequence to decode (one line per sequence)")
parser.add_argument('-tgt',   help="True target sequence (optional)")
parser.add_argument('-output', default='pred.txt', help="Path to output the predictions (each line will be the decoded sequence")

# beam search options

parser.add_argument('-beam_size',  type=int, default=5,  help="Beam size")
parser.add_argument('-batch_size', type=int, default=30, help="Batch size")
parser.add_argument('-max_sent_length', default=250, help="Maximum sentence length. If any sequences in srcfile are longer than this then it will error out")
parser.add_argument('-replace_unk', action="store_true", help= \
                    """Replace the generated UNK tokens with the source token that
                    had the highest attention weight. If phrase_table is provided,
                    it will lookup the identified source token and give the corresponding
                    target token. If it is not provided (or the identified source token
                    does not exist in the table) then it will copy the source token""")
# parser.add_argument('-phrase_table', help="""Path to source-target dictionary to replace UNK
#                     tokens. See README.md for the format this file should be in""")

parser.add_argument('-verbose', action="store_true", help="Print scores and predictions for each sentence")
parser.add_argument('-n_best', type=int, default=1, help="If > 1, it will also output an n_best list of decoded sentences")

## **Other options**

parser.add_argument('-cuda', action="store_true", help="ID of the GPU to use (-1 = use CPU, 0 = let cuda choose between available GPUs)")

def reportScore(name, scoreTotal, wordsTotal):
    print(name + " AVG SCORE. %.4f, " + name + " PPL: %.4f" % (
        scoreTotal / wordsTotal, math.exp(-scoreTotal/wordsTotal)))


def main():
    opt = parser.parse_args()

    translator = onmt.Translator(opt)

    outF = open(opt.output, 'w')

    predScoreTotal, predWordsTotal, goldScoreTotal, goldWordsTotal = 0, 0, 0, 0

    start = time.time()

    srcBatch, tgtBatch = [], []

    count = 0
    tgtF = open(opt.tgt) if opt.tgt else None
    for line in open(opt.src):
        count += 1

        # FIXME: features? need to use extract from preprocess.py
        srcTokens = line.split()
        tgtTokens = tgtF.readline().split() if tgtF else None

        srcBatch += [srcTokens]
        tgtBatch += [tgtTokens]

        if len(srcBatch) < opt.batch_size:
            continue

        predBatch, info = onmt.translate.Translator.translate(srcBatch, tgtBatch)

        predScoreTotal += sum(x.score for x in info)
        predWordsTotal += sum(len(x) for x in predBatch)
        if tgtF is not None:
            goldScoreTotal += sum(x.goldScore for x in info)
            goldWordsTotal += sum(len(x) for x in tgtBatch)

        for b in range(len(predBatch)):
            outFile.write(" ".join(predBatch[b]) + '\n')

            if opt.verbose:
                print('SENT ' + count + '. ' + " ".join(srcBatch[b]))
                print('PRED ' + count + '. ' + " ".join(predBatch[b]))
                print("PRED SCORE: %.4f" % info[b].score)

                if tgtF is not None:
                    print('GOLD ' + count + '. ' + " ".join(tgtBatch[b]))
                    print("GOLD SCORE: %.4f" % info[b].goldScore))

                if opt.n_best > 1:
                    print('\nBEST HYP:')
                    for pred in info[b].nBest:
                        print("[%.4f] %s" % (pred.score, " ".join(pred.tokens)))

                print('')


    reportScore('PRED', predScoreTotal, predWordsTotal)
    if tgtF:
        reportScore('GOLD', goldScoreTotal, goldWordsTotal)

    if tgtF:
        tgtF.close()


if __name__ == "main":
    main()

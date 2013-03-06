import csv
import logging
import optparse
import os
import re
import sys
import tempfile
import yaml

NO_ORIGINAL=True

def getcsv(name, instance, data, log):
  csvfile = tempfile.NamedTemporaryFile(delete = False, suffix=".csv")
  datawriter = csv.writer(csvfile, delimiter=',')
  datawriter.writerow(['datasize', 'original', 'pbesparelm', 'pbesstategraph'])
  rows = []
  
  for (case, instances) in data.items():
    if case.startswith('{0} '.format(name)):
      DATA_RE = 'datasize=(?P<d>\d+)'
      m = re.search(DATA_RE, case, re.DOTALL)
      if m is not None:
        datasize = m.groupdict()['d']
        rows.append([datasize, instances[instance].setdefault('original',{}).setdefault('sizes', {}).setdefault('eqns', 'NaN'), instances[instance]['pbesparelm']['sizes']['eqns'], instances[instance]['pbesstategraph']['sizes']['eqns']])
      else:
        log.error('Case {0}, which matches {1} does not have a datasize parameter')
        sys.exit(1)
        
  for row in sorted(rows, cmp=lambda x,y: cmp(int(x[0]), int(y[0]))):
    datawriter.writerow(row)
  csvfile.close()
  return csvfile.name

def plot(name, instance, data, outfilename, xlogscale, ylogscale, log):
  csvfilename = getcsv(name, instance, data, log)
  log.info("CSV written to {0}".format(csvfilename))
  logarithm=''
  if xlogscale:
    logarithm.append('x')
  if ylogscale:
    logarithm.append('y')
  
  
  RSCRIPT = '''
csv_data <- read.csv("{csvfilename}", header=T, sep=',')
plot_colors <- c("blue", "red", "forestgreen")
# Trim off excess margin space (bottom, left, top, right)
par(mar=c(4.2, 3.8, 0.2, 0.2))
ylim=range(c(csv_data$original,csv_data$pbesparelm,csv_data$pbesstategraph), na.rm = TRUE, finite = TRUE)
pdf(file="{outfilename}", height=3.5, width=5)
plot(csv_data$datasize, csv_data$original, type="b", {logscale}
     col=plot_colors[1], ylim=ylim,
  axes=T, ann=T, xlab="|D|",
  ylab="nr. equations")
lines(csv_data$datasize, csv_data$pbesparelm, type="b", col=plot_colors[2], lty=2)
lines(csv_data$datasize, csv_data$pbesstategraph, type="b", col=plot_colors[3], lty=2)

legend("topleft", names(csv_data[2:4]), col=plot_colors, lty=1:3, bty="n");
box()

# Turn off device driver (to flush output to PDF)
dev.off()

# Restore default margins
par(mar=c(5, 4, 4, 2) + 0.1)

'''.format(csvfilename=csvfilename,
           outfilename=outfilename,
           logscale='log="{0}",'.format(logarithm) if logarithm != '' else '')

  rfile = tempfile.NamedTemporaryFile(delete = False, suffix=".rscript")
  rfile.write(RSCRIPT)
  rfile.close()
  
  os.system("Rscript {0}".format(rfile.name))
  
  log.info("R Script written to {0}".format(rfile.name))
  
def run(infilename, outfilename, name, instance, xlogscale, ylogscale, log):
  data = yaml.load(open(infilename).read())
  
  plot(name, instance, data, outfilename, xlogscale, ylogscale, log)
  
def runCmdLine():
  parser = optparse.OptionParser(usage='usage: %prog [options] infile outfile')
  parser.add_option('-v', action='count', dest='verbosity',
                    help='Be more verbose. Use more than once to increase verbosity even more.')
  parser.add_option('--lx', action='store_true', dest='xlogscale',
                    help='Use logscale for x-axis')
  parser.add_option('--ly', action='store_true', dest='ylogscale',
                    help='Use logscale for y-axis')
  parser.add_option('-n', '--name', dest='name',
                    help='Generate plot for problem NAME', metavar='NAME',
                    default='Lossy buffer')
  parser.add_option('-i', '--instance', dest='instance',
                    help='Generate plot for problem INSTANCE', metavar='INSTANCE',
                    default='received_no_other_read_then_delivered')
  options, args = parser.parse_args()
  if len(args) < 2:
    parser.error(parser.usage)
  
  infilename = args[0]
  outfilename = args[1]

  logging.basicConfig()
  if options.verbosity > 0:
    logging.getLogger('plot').setLevel(logging.INFO)
  
  run(infilename, outfilename, options.name, options.instance, options.xlogscale, options.ylogscale, logging.getLogger('plot'))

if __name__ == '__main__':
  runCmdLine()
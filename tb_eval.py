from tbparse import SummaryReader
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import seaborn as sns
from tqdm import tqdm
from argparse import ArgumentParser


parser = ArgumentParser("Training evaluation")
parser.add_argument("--source_path", "-s", required=True, type=str)
parser.add_argument("--no_csv", action='store_true', help="Don't export training metrics as csv")
parser.add_argument("--no_scal", action='store_true', help="Don't plot curves from training scalars")
parser.add_argument("--no_hist", action='store_true', help="Don't plot opacity curves")
parser.add_argument("--no_img", action='store_true', help="Don't export rendered training images")
parser.add_argument("--render", nargs="+", type=int, default=[0, 3], help="Viewport indices to render")
args = parser.parse_args()

log_dir = args.source_path
print("Reading tb file in " + log_dir)
reader = SummaryReader(log_dir)
print("Finished reading tb file. Starting exports...")

df_scal = reader.scalars

# unique steps and tags as columns with values
df_scal = df_scal.pivot(index='step', columns='tag', values='value')
df_scal.columns.name = None
df_scal.index.name = "iteration"
df_scal.reset_index(inplace=True)

# evaluation metrics (at test iterations)
df_eval_metrics = df_scal.dropna()
df_eval_metrics.drop(columns=['train_loss_patches/l1_loss', 'train_loss_patches/total_loss'], inplace=True)
df_eval_metrics.rename(columns={'iteration': 'iterations'}, inplace=True)
df_eval_metrics.insert(0, 'model', os.path.basename(log_dir))

# training metrics
df_train_metrics = df_scal.dropna(axis=1, how='any')


export_folder = log_dir + "/eval"
os.makedirs(export_folder, exist_ok=True)


# export training and evaluation metrics as csv
if(not args.no_csv):
    #export training metrics as csv
    df_train_metrics.to_csv(export_folder + '/training_process.csv', index=False)
    df_eval_metrics.to_csv(export_folder + '/eval_metrics.csv', index=False)

    print("Exported training metrics csv to " + export_folder)


# plot training curves
if(not args.no_scal):
    plot_folder = log_dir + '/eval/plots'
    os.makedirs(plot_folder, exist_ok=True)

    # plot training loss curves
    sns.set_style("darkgrid")
    sns.set_palette("tab10")
    plt.figure(figsize=(12, 8))
    plt.title('Training loss', fontsize=18)
    plt.plot(df_train_metrics['train_loss_patches/l1_loss'], label='L1 loss', linewidth=0.5, alpha=0.8)
    plt.plot(df_train_metrics['train_loss_patches/total_loss'], label='Total loss', linewidth=0.5, alpha=0.8)
    plt.xlabel('Iteration')
    plt.ylabel('Loss')
    plt.legend()

    # after plotting the data, format the labels
    current_values_x = plt.gca().get_xticks()

    # using format string '{:.0f}' here but you can choose others
    plt.gca().set_xticklabels(['{:,.0f}'.format(x) for x in current_values_x])

    # export plot as png
    plt.savefig(plot_folder + '/training_loss.png', bbox_inches='tight')
    
    print("Exported training loss plot to " + plot_folder)


    # plot L1 loss curves
    sns.set_style("darkgrid")
    sns.set_palette("tab10")
    plt.figure(figsize=(12, 8))
    plt.title('L1 loss', fontsize=18)
    plt.plot(df_eval_metrics['train/loss_viewpoint - l1_loss'], label='Train', lw=2)
    plt.plot(df_eval_metrics['test/loss_viewpoint - l1_loss'], label='Test', lw=2)
    plt.xlabel('Iteration')
    plt.ylabel('L1 loss')
    plt.legend()

    # after plotting the data, format the labels
    current_values_x = plt.gca().get_xticks()

    # using format string '{:.0f}' here but you can choose others
    plt.gca().set_xticklabels(['{:,.0f}'.format(x) for x in current_values_x])

    # export plot as png
    plt.savefig(plot_folder + '/l1_loss.png', bbox_inches='tight')

    print("Exported L1 loss plot to " + plot_folder)


    # plot psnr curves
    sns.set_style("darkgrid")
    sns.set_palette("tab10")
    plt.figure(figsize=(12, 8))
    plt.title('PSNR', fontsize=18)
    plt.plot(df_eval_metrics['train/loss_viewpoint - psnr'], label='Train', lw=2)
    plt.plot(df_eval_metrics['test/loss_viewpoint - psnr'], label='Test', lw=2)
    plt.xlabel('Iteration')
    plt.ylabel('PSNR')
    plt.legend()

    # after plotting the data, format the labels
    current_values_x = plt.gca().get_xticks()

    # using format string '{:.0f}' here but you can choose others
    plt.gca().set_xticklabels(['{:,.0f}'.format(x) for x in current_values_x])

    # export plot as png
    plt.savefig(plot_folder + '/psnr.png', bbox_inches='tight')

    print("Exported PSNR plot to " + plot_folder)


    # plot total points
    sns.set_style("darkgrid")
    sns.set_palette("tab10")
    plt.figure(figsize=(12, 8))
    plt.title('Total points', fontsize=18)
    plt.plot(df_eval_metrics['total_points'], lw=2)
    plt.xlabel('Iteration')
    plt.ylabel('Total points')

    # after plotting the data, format the labels
    current_values_x = plt.gca().get_xticks()
    current_values_y = plt.gca().get_yticks()

    # using format string '{:.0f}' here but you can choose others
    plt.gca().set_xticklabels(['{:,.0f}'.format(x) for x in current_values_x])
    plt.gca().set_yticklabels(['{:,.0f}'.format(x) for x in current_values_y])

    # export plot as png
    plt.savefig(plot_folder + '/total_points.png', bbox_inches='tight')

    print("Exported total points plot to " + plot_folder)


# plot opacity curves
if(not args.no_hist):
    plot_folder = log_dir + '/eval/plots'
    os.makedirs(plot_folder, exist_ok=True)

    df_hist = reader.histograms

    # Calculate total counts for limits < 0.5 and limits >= 0.5 for each step
    df_hist['counts_less_than_0.5'] = df_hist.apply(lambda row: row['counts'][row['limits'] < 0.5].sum(), axis=1)
    df_hist['counts_greater_than_or_equal_0.5'] = df_hist.apply(lambda row: row['counts'][row['limits'] >= 0.5].sum(), axis=1)

    sns.set_style("darkgrid")
    sns.set_palette("tab10")

    # Initialize the figure
    plt.figure(figsize=(12, 8))

    # Plot counts for limits < 0.5
    plt.plot(df_hist['step'], df_hist['counts_less_than_0.5'], label='Opacity < 0.5', lw=2)

    # Plot counts for limits >= 0.5
    plt.plot(df_hist['step'], df_hist['counts_greater_than_or_equal_0.5'], label='Opacity >= 0.5', lw=2)

    # Add title and labels
    plt.title('Low vs. high opacity gaussians', fontsize=18)
    plt.xlabel('Iteration')
    plt.ylabel('Count')

    # Add legend
    plt.legend()

    # after plotting the data, format the labels
    current_values_x = plt.gca().get_xticks()
    current_values_y = plt.gca().get_yticks()

    # using format string '{:.0f}' here but you can choose others
    plt.gca().set_xticklabels(['{:,.0f}'.format(x) for x in current_values_x])
    plt.gca().set_yticklabels(['{:,.0f}'.format(x) for x in current_values_y])

    # Export plot as png
    plt.savefig(plot_folder + '/opacity_low_vs_high.png', bbox_inches='tight')

    print("Exported low vs. high opacity plot to " + plot_folder)

    
    # only keep every 1000th histogram
    df_hist_reduced = df_hist[df_hist['step'] % 1000 == 0]

    sns.set_style("darkgrid")
    sns.set_palette("magma", 7)
    plt.figure(figsize=(12, 8))

    def plot_subplots(data, label):
        counts = data['counts'].iloc[0]
        limits = data['limits'].iloc[0]
        x, y = SummaryReader.histogram_to_bins(counts, limits, limits[0], limits[-1], 15)
        # Draw the densities in a few steps
        plt.plot(x, y, lw=2, label=label)

    # Plot each histogram
    for i, step in enumerate(df_hist_reduced['step']):
        plot_subplots(df_hist_reduced[df_hist_reduced['step'] == step], f'Iteration {step}')

    plt.title('Gaussians per opacity', fontsize=18)
    plt.xlabel('Opacity')
    plt.ylabel('Count')
    plt.legend()

    # after plotting the data, format the labels
    current_values_y = plt.gca().get_yticks()

    # using format string '{:.0f}' here but you can choose others
    plt.gca().set_yticklabels(['{:,.0f}'.format(x) for x in current_values_y])

    # export plot as png
    plt.savefig(plot_folder + '/opacity_count.png', bbox_inches='tight')
    
    print("Exported Gaussians per opacity plot to " + plot_folder)


# export rendered images from training
if(not args.no_img):
    df_img = reader.images

    img_tags = df_img['tag'].unique()
    render_tags = [img_tags[i] for i in args.render] # ['test_view_0161/render', 'test_view_0049/render']

    for render_tag in render_tags:
        print("Exporting " + render_tag + " images...")
        render_folder = log_dir + '/eval/' + render_tag
        os.makedirs(render_folder, exist_ok=True)
        counter = int(1)
        total_images = str()
        progress_bar = tqdm(range(0, len(df_img[df_img['tag'] == render_tag])), desc="Images rendered")

        for i in df_img.index:
            if df_img.loc[i, 'tag'] != render_tag:
                continue
            
            #print("Exporting image " + str(counter) + "/" + total_images + "...")
            image = df_img.loc[i, 'value']
            height, width, _ = image.shape
            plt.figure(figsize=(width/80, height/80), dpi=80)
            plt.imshow(image)
            plt.axis('off')
            plt.box(False)
            plt.savefig(render_folder + '/' + str(counter) + '.png', bbox_inches='tight', pad_inches=0, transparent=True, dpi=300)
            plt.close()

            progress_bar.update(1)
            counter += 1
        
        progress_bar.close()
        print("Exported " + render_tag + " images to " + render_folder)
    print("Finished exporting images")

print("Finished all exports")
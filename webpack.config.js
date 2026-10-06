const MiniCssExtractPlugin = require('mini-css-extract-plugin');

devMode = process.env.NODE_ENV === 'development';

module.exports = {
    entry: './src/mpships_infra/index.js',
    plugins: [
        new MiniCssExtractPlugin({
            // Options similar to the same options in webpackOptions.output
            // both options are optional
            // filename: devMode ? '[name].css' : '[name].[chunkhash].css',
            filename: devMode ? 'mpships.css' : 'mpships.css',
            chunkFilename: devMode ? '[id].css' : '[id].[chunkhash].css',
        }),
    ],
    module: {
        rules: [
            {
                test: /\.(sa|sc|c)ss$/,
                use: [
                    {
                        loader: MiniCssExtractPlugin.loader,
                        options: {
                            esModule: true,
                        },
                    },
                    'css-loader',
                    'sass-loader'
                ],
            },
            {
                test: /\.(woff(2)?|ttf|eot|svg)(\?v=\d+\.\d+\.\d+)?$/,
                type: 'asset/resource',
                generator: {
                    filename: './fonts/[name].[hash][ext]',
                }
            }
        ]
    },
};

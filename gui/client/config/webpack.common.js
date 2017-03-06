const webpack = require("webpack");
const HtmlWebpackPlugin = require('html-webpack-plugin');
const ExtractTextPlugin = require('extract-text-webpack-plugin');
const helpers = require('./helpers');

module.exports = {
        entry: {
        'polyfills': ['./polyfills.js'],
        'vendor': ['./vendor.js', "bootstrap-webpack2!./bootstrap.config.js"],
        'app': './main.js'
    },
    resolve: {
        extensions: ['.js'],
        alias: {
            leaflet_css: helpers.root("/node_modules/leaflet/dist/leaflet.css"),
            leaflet_marker: helpers.root("/node_modules/leaflet/dist/images/marker-icon.png"),
            leaflet_marker_2x: helpers.root("/node_modules/leaflet/dist/images/marker-icon-2x.png"),
            leaflet_marker_shadow: helpers.root("/node_modules/leaflet/dist/images/marker-shadow.png"),

            leaflet_loading_css: helpers.root("/node_modules/leaflet-loading/src/Control.Loading.css"),
            contextmenu_items_css: helpers.root("/node_modules/leaflet-contextmenu/dist/leaflet.contextmenu.css"),

            jquery: helpers.root("/jquery-stub.js")
        }
    },
    module: {
        rules: [
            {test: /\.js$/, exclude: /node_modules/, use: ["babel-loader"]},
            {test: /\.html$/, use: ['html-loader']},
            {
                test: /\.css$/,
                use: ExtractTextPlugin.extract({fallback: 'style-loader', use: 'css-loader'})
            },
            {
                test: /\.(woff|woff2)(\?v=\d+\.\d+\.\d+)?$/,
                use: ['url-loader?limit=10000&mimetype=application/font-woff']
            },
            {test: /\.ttf(\?v=\d+\.\d+\.\d+)?$/, use: ['url-loader?limit=10000&mimetype=application/octet-stream']},
            {test: /\.eot(\?v=\d+\.\d+\.\d+)?$/, use: ['file-loader']},
            {test: /\.svg(\?v=\d+\.\d+\.\d+)?$/, use: ['url-loader?limit=10000&mimetype=image/svg+xml']},
            {test: /\.(png|jpg|gif)$/, use: ["file-loader?name=images/[name].[ext]"]},
            {test: /\.svg/, use: ['svg-url-loader']},
            {test: /\.less$/, use: ["style-loader!css-loader!less-loader"]},
        ]
    },

    devtool: 'source-map',

    plugins: [
        new webpack.optimize.CommonsChunkPlugin({
            name: ['app', 'vendor', 'polyfills']
        }),
        new HtmlWebpackPlugin({
            template: 'index.html'
        })
    ]
};
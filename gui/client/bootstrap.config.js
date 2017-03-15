'use strict';
// ## bootstrap-webpack Configuration

module.exports = {
    // styleLoader: require('extract-text-webpack-plugin').extract({ fallback: 'style-loader', use: ['css-loader,less-loader']}),
    // ### Scripts
    // Any scripts here set to false will never
    // make it to the client, it's not packaged
    // by webpack.
    scripts: {
        'transition': false,
        'alert': false,
        'button': false,
        'carousel': false,
        'collapse': false,
        'dropdown': false,
        'modal': false,
        'tooltip': false,
        'popover': false,
        'scrollspy': false,
        'tab': false,
        'affix': false
    },
    // ### Styles
    // Enable or disable certapin less components and thus remove
    // the css for them from the build.
    styles: {
        "mixins": true,

        "normalize": true,
        "print": false,

        "scaffolding": true,
        "type": false,
        "code": false,
        "grid": true,
        "tables": false,
        "forms": true,
        "buttons": true,

        "component-animations": false,
        "glyphicons": false,
        "dropdowns": true,
        "button-groups": true,
        "input-groups": true,
        "navs": false,
        "navbar": false,
        "breadcrumbs": false,
        "pagination": false,
        "pager": false,
        "labels": true,
        "badges": true,
        "jumbotron": false,
        "thumbnails": false,
        "alerts": true,
        "progress-bars": false,
        "media": true,
        "list-group": true,
        "panels": true,
        "wells": true,
        "close": true,

        "modals": false,
        "tooltip": false,
        "popovers": false,
        "carousel": false,

        "utilities": true,
        "responsive-utilities": true
    }
};
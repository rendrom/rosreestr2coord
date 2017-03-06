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
        "print": true,

        "scaffolding": true,
        "type": true,
        "code": true,
        "grid": true,
        "tables": true,
        "forms": true,
        "buttons": true,

        "component-animations": true,
        "glyphicons": true,
        "dropdowns": true,
        "button-groups": true,
        "input-groups": true,
        "navs": true,
        "navbar": true,
        "breadcrumbs": true,
        "pagination": true,
        "pager": true,
        "labels": true,
        "badges": true,
        "jumbotron": true,
        "thumbnails": true,
        "alerts": true,
        "progress-bars": true,
        "media": true,
        "list-group": true,
        "panels": true,
        "wells": true,
        "close": true,

        "modals": true,
        "tooltip": true,
        "popovers": true,
        "carousel": true,

        "utilities": true,
        "responsive-utilities": true
    }
};
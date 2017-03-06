import 'core-js/es6';
// import 'core-js/es7/reflect';
// import 'whatwg-fetch';

if (process.env.ENV === 'production') {
    // Production
} else {
    // Development
    Error['stackTraceLimit'] = Infinity;

}
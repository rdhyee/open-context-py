(function(window) {
    var HAS_HASHCHANGE = (function() {
        var doc_mode = window.documentMode;
        return ('onhashchange' in window) &&
            (doc_mode === undefined || doc_mode > 7);
    })();
    
    L.Hash = function(map) {
        this.tile_zoom = false;
        this.onHashChange = L.Util.bind(this.onHashChange, this);
    
        if (map) {
            this.init(map);
        }
    };
    
    L.Hash.prototype = {
        map: null,
        lastHash: null,
    
        contains: function(a, obj) {
            var i = a.length;
            while (i--) {
               if (a[i] === obj) {
                   return true;
               }
            }
            return false;
        },

        parseHash: function(hash) {
            if(hash.indexOf('#') == 0) {
                hash = hash.substr(1);
            }
            var args = hash.split("/");
            if (args.length >= 3) {
                var zoom = parseInt(args[0], 10),
                    lat = parseFloat(args[1]),
                    lon = parseFloat(args[2]);
                if (isNaN(zoom) || isNaN(lat) || isNaN(lon)) {
                    return false;
                } else {
                    
                    if (args.length > 3) {
                        //map geo tile depth
                        if (this.map.hasOwnProperty('geodeep')) {
                            //map geo tile depth
                            var geodeep = parseInt(args[3], 10);
                            if (!isNaN(geodeep)) {
                                this.map.geodeep = geodeep;
                            }
                        }
                    }
                    if (args.length >= 4) {
                        //map layer type to display
                        if (this.map.hasOwnProperty('default_layer')) {
                            this.map.default_layer = false;
                            if (args[4] != 'false') {
                                // type of map layer to display
                                this.map.default_layer = args[4];
                            }
                        }
                    }
                    return {
                        center: new L.LatLng(lat, lon),
                        zoom: zoom
                    };
                }
            } else {
                return false;
            }
        },
    
        formatHash: function(map) {
            var center = map.getCenter(),
                zoom = map.getZoom(),
                precision = Math.max(0, Math.ceil(Math.log(zoom) / Math.LN2));
            if (this.map.hasOwnProperty('geodeep')) {
                var default_layer = 'false';
                if (this.map.hasOwnProperty('default_layer')) {
                    var default_layer = this.map.default_layer; 
                }
                return "#" + [
                    zoom,
                    center.lat.toFixed(precision),
                    center.lng.toFixed(precision),
                    this.map.geodeep,
                    default_layer
                ].join("/");
            }
            else{
                return "#" + [zoom,
                    center.lat.toFixed(precision),
                    center.lng.toFixed(precision)
                ].join("/");
            }
        },
    
        init: function(map) {
            this.map = map;
            
            this.map.on("moveend", this.onMapMove, this);
            
            // reset the hash
            this.lastHash = null;
            this.onHashChange();
    
            if (!this.isListening) {
                this.startListening();
            }
        },
    
        remove: function() {
            this.map = null;
            if (this.isListening) {
                this.stopListening();
            }
        },
        
        onMapMove: function(map) {
            // bail if we're moving the map (updating from a hash),
            // or if the map has no zoom set
            
            if (this.movingMap || this.map.getZoom() === 0) {
                return false;
            }
            
            var hash = this.formatHash(this.map);
            if (this.lastHash != hash) {
                location.replace(hash);
                this.lastHash = hash;
            }
        },
    
        movingMap: false,
        update: function() {
            var hash = location.hash;
            if (hash === this.lastHash) {
                // console.info("(no change)");
                return;
            }
            var parsed = this.parseHash(hash);
            if (parsed) {
                // console.log("parsed:", parsed.zoom, parsed.center.toString());
                this.movingMap = true;
                
                this.map.setView(parsed.center, parsed.zoom);
                
                this.movingMap = false;
            } else {
                // console.warn("parse error; resetting:", this.map.getCenter(), this.map.getZoom());
                this.onMapMove(this.map);
            }
        },
    
        // defer hash change updates every 100ms
        changeDefer: 100,
        changeTimeout: null,
        onHashChange: function() {
            // throttle calls to update() so that they only happen every
            // `changeDefer` ms
            if (!this.changeTimeout) {
                var that = this;
                this.changeTimeout = setTimeout(function() {
                    that.update();
                    that.changeTimeout = null;
                }, this.changeDefer);
            }
        },
    
        isListening: false,
        hashChangeInterval: null,
        startListening: function() {
            if (HAS_HASHCHANGE) {
                L.DomEvent.addListener(window, "hashchange", this.onHashChange);
            } else {
                clearInterval(this.hashChangeInterval);
                this.hashChangeInterval = setInterval(this.onHashChange, 50);
            }
            this.isListening = true;
        },
    
        stopListening: function() {
            if (HAS_HASHCHANGE) {
                L.DomEvent.removeListener(window, "hashchange", this.onHashChange);
            } else {
                clearInterval(this.hashChangeInterval);
            }
            this.isListening = false;
        }
    };
})(window);
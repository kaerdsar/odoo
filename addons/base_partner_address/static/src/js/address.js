openerp.lr_partner_address = function (instance) {

    var QWeb = instance.web.qweb;

    // 58 is the identifier for Germany
    var default_country_value = 58;

    instance.web.list.columns.add('field.address', 'instance.web.list.AddressColumn');

    instance.web.list.AddressColumn = instance.web.list.Column.extend({
        _format: function (row_data, options) {
            var address = $.parseJSON(row_data.address.value);
            return QWeb.render('AddressColumn', {
                street: address.street,
                street2: address.street2,
                city: address.city,
                zip: address.zip,
                country: address.country_id ? address.country_id[1] : ''
            });
        }
    });

    instance.web.form.widgets.add('address', 'instance.web.form.Address');

    instance.web.form.Address = instance.web.form.AbstractField.extend(instance.web.form.ReinitializeFieldMixin, {
        template: 'Address',
        start: function() {
            var _super = this._super();
            var self = this;
            this.$el.on('change', 'input, select', function(e) {
                self.internal_set_value(self.get_value());
            });

            try {
                var address = JSON.parse(this.getParent().datarecord.address);
                var country = address.country_id ? address.country_id[0] : default_country_value
            }
            catch (e) {
                var country = default_country_value;
            }

            var countries = this.$el.find('select[name="country_id"]');
            if (countries.has('option').length == 0) {
                openerp.jsonRpc('/web/dataset/call_kw', 'call', {
                    model: 'res.country',
                    method: 'search_read',
                    args: [[], ['id', 'name']],
                    kwargs: {}
                }).then(function(data) {
                    _.each(data, function(d){
                        var option = "<option ";
                        if (d.id == country) {
                            option += "selected";
                        }
                        option += "/>";
                        countries.append($(option).val(d.id).text(d.name));
                    });
                });
            }

            this.flag_focus = true;
            this.$el.on('focus', 'input[name="city"]', function(event) {
                if (self.flag_focus) {
                    self.$el.find('input[name="street"]').focus();
                    self.flag_focus = false;
                }
            });

            var inputs = this.$el.find('input, select');
            this.$el.on('keydown', function(event) {
                var index = inputs.index(event.target);
                if(event.shiftKey && event.keyCode == 9) {
                    if (index != 0) {
                        $(inputs[index - 1]).focus();
                        return false;
                    }
                }
                else if (event.keyCode == 9) {
                    if (index != inputs.length - 1) {
                        $(inputs[index + 1]).focus();
                        return false;
                    }
                }
            });

            if (this.getParent().datarecord.address) {
                this.set_value(this.getParent().datarecord.address);
            }
            return _super;
        },
        set_value: function(value) {
            var address = JSON.parse(value);
            var country_id = this.get_country_id(address);
            this.$el.find('input[name="street"]').val(address.street);
            this.$el.find('input[name="street2"]').val(address.street2);
            this.$el.find('input[name="zip"]').val(address.zip);
            this.$el.find('input[name="city"]').val(address.city);
            this.$el.find('select[name="country_id"]').val(country_id);
            this._super(value);
        },
        get_value: function() {
            var address = {
                'street': this.$el.find('input[name="street"]').val(),
                'street2': this.$el.find('input[name="street2"]').val(),
                'zip': this.$el.find('input[name="zip"]').val(),
                'city': this.$el.find('input[name="city"]').val(),
                'country_id': this.$el.find('select[name="country_id"]').val(),
            }
            return JSON.stringify(address);
        },
        render_value: function() {
            this.flag_focus = true;
            var countries = this.$el.find('select[name="country_id"]');
            if (!countries.val()) {
                countries.val(default_country_value);
            }
            this._super();
        },
        get_country_id: function(address) {
            if (address && address.country_id) {
                if (typeof address.country_id == 'object') {
                    return address.country_id[0];
                }
                else {
                    return address.country_id;
                }
            }
            return default_country_value;
        }
    });

};

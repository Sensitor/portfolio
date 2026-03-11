public class DemiOrque extends Race {
    public DemiOrque() {
        super("Demi-Orque");
    }

    @Override
    public void appliquerModificateurs(Personnage p) {
        p.getForce().set(p.getForce().get() + 2);
        p.getIntelligence().set(p.getIntelligence().get() - 2);
        p.getCharisme().set(p.getCharisme().get() - 2);
    }
}
